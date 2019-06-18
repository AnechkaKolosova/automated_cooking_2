import {Component, OnInit} from '@angular/core';
import {DeviceService} from '../_services/device.service';
import {Device} from '../_models/device';
import {NotificationService} from '../_services/notification.service';
import {take} from 'rxjs/operators';

@Component({
  selector: 'app-device-list',
  templateUrl: './device-list.component.html',
  styleUrls: ['./device-list.component.scss']
})
export class DeviceListComponent implements OnInit {
  devices: Device[];

  constructor(private deviceService: DeviceService, private notificationService: NotificationService) {

  }

  ngOnInit() {
    this.deviceService.newDeviceCreated.pipe(take(1)).subscribe(device => {
      this.devices.push(device);
    });
    this.deviceService.readDevices().subscribe(devices => {
      console.log(devices);
      this.devices = devices;
    });
    this.notificationService.messages.subscribe(msg => {
      console.log(msg);
      const foundDevice: Device | undefined = this.devices.find((dv, index, array) => {
        return dv.id === msg.device;
      });
      if (foundDevice) {
        if (msg.type === 'show_temp') {
          foundDevice.temp = msg.temp;
          foundDevice.photo = msg.photo;
          foundDevice.longitude = msg.longitude;
          foundDevice.latitude = msg.latitude;
          foundDevice.humidity = msg.humidity;
        } else {
          console.log('Unknown msg');
        }
      }
    });
  }

}
