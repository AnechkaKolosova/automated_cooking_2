import {Injectable} from '@angular/core';
import {Message} from '../_models/message';
import {Observable, Subject} from 'rxjs';
import {WebsocketService} from './websocket.service';
import {map, publish, share} from 'rxjs/operators';
import {environment} from '../../environments/environment';
import {AuthService} from './auth.service';
import {SetTemp} from '../_models/setTemp';

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  public messages: Observable<Message>;
  private ws: Subject<any>;

  constructor(private wsService: WebsocketService, private authService: AuthService) {
    this.ws = wsService.connect(`${environment.wsUrl}?token=${authService.token}`);
    this.messages = this.ws.pipe(
      map((response: any): Message => {
        const data = JSON.parse(response.data);
        return {
          type: data.type,
          device: data.device,
          temp: data.temp,
          photo: data.photo,
          latitude: data.latitude,
          longitude: data.longitude,
          humidity: data.humidity
        };
      }), share());
  }

  sendMsg(msg: any) {
    console.log(msg);
    this.ws.next(msg);
  }
}
