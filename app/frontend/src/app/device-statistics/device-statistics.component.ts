import {AfterContentInit, AfterViewChecked, AfterViewInit, Component, ElementRef, OnDestroy, OnInit, ViewChild} from '@angular/core';

import {Chart} from 'chart.js';
import {Metric} from '../_models/metric';
import {StatisticsService} from '../_services/statistics.service';
import {interval, of, Subscription} from 'rxjs';
import {delay, startWith, switchMap, take} from 'rxjs/operators';

@Component({
  selector: 'app-device-statistics',
  templateUrl: './device-statistics.component.html',
  styleUrls: ['./device-statistics.component.scss']
})
export class DeviceStatisticsComponent implements OnInit, OnDestroy {

  @ViewChild('canvas') canvas: ElementRef;
  title = 'stats';
  data: Metric[];
  time = [];
  hum = [];
  temp = [];
  chart: Chart;
  private subscription: Subscription;

  constructor(private statService: StatisticsService) {
  }

  ngOnInit() {

    this.statService.initStatProcess().subscribe(res => {
    }, e => {
    });
    this.statService.getStats().subscribe(metrics => {
      console.log(metrics);
      metrics.forEach(metric => {
        console.log(metric);
        if (this.time.length > 20) {
          this.time.shift();
        }
        if (this.hum.length > 20) {
          this.hum.shift();
        }
        if (this.temp.length > 20) {
          this.temp.shift();
        }
        this.time.push(new Date(metric.dt).getMinutes());
        this.hum.push(metric.humidity);
        this.temp.push(metric.temp);
      });
      console.log(this.time);
      console.log(this.hum);
      console.log(this.temp);
      interval(2000).pipe(take(2)).subscribe(() => {
        this.chart = new Chart('canvas', {
          type: 'line',
          data: {
            labels: this.time,
            datasets: [
              {
                label: 'temperature',
                yAxisID: 'temperature',
                data: this.temp,
                borderColor: '#44ba3c',
                fill: false
              },
              {
                label: 'humidity',
                yAxisID: 'humidity',
                data: this.hum,
                borderColor: '#4d81ba',
                fill: false
              },
            ]
          },
          options: {
            legend: {
              display: false
            },
            scales: {
              xAxes: [{
                display: true
              }],
              yAxes: [{
                id: 'temperature',
                type: 'linear',
                position: 'left',
                display: true
              },
                {
                  id: 'humidity',
                  type: 'linear',
                  position: 'right',
                  ticks: {
                    max: 1,
                    min: 0
                  },
                  display: true
                }],
            }
          }
        });
      });
    });
    this.subscription = interval(10000).pipe(switchMap(() => this.statService.getLatestStat())).subscribe(metrics => {
      const metric = metrics[0];
      if (metric) {
        if (this.time.length > 20) {
          this.time.shift();
        }
        if (this.hum.length > 20) {
          this.hum.shift();
        }
        if (this.temp.length > 20) {
          this.temp.shift();
        }
        if (this.time[this.time.length - 1] !== new Date(metric.dt)) {
          this.time.push(new Date(metric.dt).getMinutes());
        }
        this.chart.update();
      }
    });


  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }

}
