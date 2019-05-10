(defproject sous_vide_microservice "0.1.0-SNAPSHOT"
  :description "FIXME: write description"
  :url "http://example.com/FIXME"
  :license {:name "EPL-2.0 OR GPL-2.0-or-later WITH Classpath-exception-2.0"
            :url "https://www.eclipse.org/legal/epl-2.0/"}
  :dependencies [[org.clojure/clojure "1.10.0"]
                 [com.taoensso/carmine "2.19.1"]
                 [org.clojure/core.async "0.4.490"]]
  :repl-options {:init-ns sous-vide-microservice.core}
  :main sous-vide-microservice.core/-main)