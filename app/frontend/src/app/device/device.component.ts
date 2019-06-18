import {Component, Input, OnInit} from '@angular/core';
import {Device} from '../_models/device';
import {MatDialog} from '@angular/material';
import {DeviceSetTemperatureComponent} from '../device-set-temperature/device-set-temperature.component';
import {AlertService} from '../_services/alert.service';

@Component({
  selector: 'app-device',
  templateUrl: './device.component.html',
  styleUrls: ['./device.component.scss']
})
export class DeviceComponent implements OnInit {

  @Input() device: Device;

  constructor(public dialog: MatDialog, private alertService: AlertService) {
  }

  ngOnInit() {
  }

}
