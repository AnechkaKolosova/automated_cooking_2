(ns sous-vide-microservice.core
  (:require [taoensso.carmine :as car]
            [clojure.core.async :as a :refer [>! <! >!! <!! go chan buffer close! thread
                                              alts! alts!! timeout go-loop alt!]]
            [clojure.data.json :as json]
            [clojurewerkz.machine-head.client :as mh]))

(defrecord Device [id user topics temp])

(defn parse-int [s]
  (Integer/parseInt (re-find #"\A-?\d+" s)))

(defn get-msg
  [topic conn ch]
  (car/with-new-pubsub-listener
    (:spec conn)
    {topic (fn [msg]
             (go (>! ch msg)))}
    (car/subscribe topic)))

(defn devices-topics
  [devices]
  (reduce-kv (fn [m _ v]
               (concat (:topics v) m))
             [] @devices))

(defn mqtt-subscribe
  [addr devices ch]
  (let [mqtt-conn (mh/connect addr)
        topics (devices-topics devices)]
    (doseq [topic topics]
      (mh/subscribe mqtt-conn {topic 0} (fn [^String topic _ ^bytes payload]
                                          (go (>! ch [topic (String. payload)])))))
    mqtt-conn))

(defn parse-msg
  [msg]
  (try
    (json/read-str msg :key-fn keyword)
    (catch Exception e (println e))))

(defn convert-msg
  [msg]
  (try
    (parse-int msg)
    (catch Exception e (println (str "Got exception while parsing mqtt msg " (.toString e))))))

(defn write-command
  [topic command ch]
  (go
    (>! ch [topic command])))

(defn handle-redis-msg
  [msg-type channel msg user-device mqtt-pub]
  (case msg-type
    "message"
    (let [converted (parse-msg msg)
          {user  :user
           device :device
           type  :type} converted]
      (case type
        "connect"
        (do (println "Msg" converted) (swap! user-device update-in [1] #(assoc % :user user)) (println @user-device))
        "set_temp"
        (do (println "Setting temp") (swap! user-device update-in [1] #(assoc % :temp (:temp converted))) (println @user-device))
        "default"))
    "subscribe"
    (println "Subscribed to" channel)))

(defn find-device
  [device-topic devices]
  (let [values (vals @devices)]
    (first (filter #(contains? (into #{} (:topics %)) device-topic) values))))

(defn process-mqtt-temp
  [ch msg topic temp-set]
  (let [temp msg]
    (cond
      (< temp (+ temp-set 0.1)) (do (println "Temp" temp) (write-command topic "1" ch))
      (> temp (+ temp-set 0.5)) (do (println "Temp" temp) (write-command topic "0" ch)))))

(defn send-redis-temp
  ([ch msg device user]
   (go (>! ch (json/write-str {"user" user, "device" device, "type" "show_temp", "temp" msg})))))

(defn send-redis-msg
  [ch msg user device]
  (let [photo (:photo msg)
        temp (:temperature_C msg)
        humidity (:humidity_% msg)
        latitude (:latitude msg)
        longitude (:longitude msg)]
    (go (>! ch (json/write-str {"type" "show_temp", "user" user, "device" device, "latitude" latitude, "longitude" longitude, "humidity" humidity, "temp" temp, "photo" photo})))))

(defn handle-mqtt-msg
  [topic payload user-device mqtt-pub-chan redis-pub-chan]
  (let [msg (parse-msg payload)
        device (find-device topic user-device)]
    (case topic
      "smuggler_00002"
      (cond
        (= (:user device) 99999) ()
        :else (do
                (send-redis-msg redis-pub-chan msg (:user device) (:id device))))
      "keyUp"
      (case msg
        0 (go (>! redis-pub-chan (json/write-str {"user" (:user device), "device" (:id device), "type" "connected"})))
        1 ())
      )))

(defn -main
  "I don't do a whole lot."
  [& args]
  (let [server1-conn {:pool {} :spec {:uri "redis://redis:6379"}}
        devices (atom {1 (Device. 1 1 ["smuggler_00002"] 40)})
        redis-sub (chan)
        mqtt-sub (chan)
        mqtt-pub (chan)
        redis-pub (chan)
        _ (get-msg "sous-vide" server1-conn redis-sub)
        mqtt_conn (mqtt-subscribe "tcp://korotach.com:1883" devices mqtt-sub)]
    (go-loop []
      (alt!
        redis-sub ([[msg-type channel msg]] (handle-redis-msg msg-type channel msg devices mqtt-pub))
        mqtt-sub ([[topic payload]] (handle-mqtt-msg topic payload devices mqtt-pub redis-pub))
        mqtt-pub ([[topic payload]] (mh/publish mqtt_conn topic payload))
        redis-pub ([payload] (do (println payload) (car/wcar server1-conn (car/publish "sous-vide" payload)))))
      (recur)))
  )


