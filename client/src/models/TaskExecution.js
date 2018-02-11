import { Decimal } from 'decimal.js'

import { naturalDay } from '@/utils.js'

function TaskExecution (id, task, day, dayOrder, duration, finished) {
  this.id = id
  this.task = task
  this.day = day
  this.dayOrder = dayOrder
  this.duration = Decimal(duration)
  this.finished = finished
}
TaskExecution.prototype.naturalDay = function () {
  return naturalDay(this.day)
}

export {
  TaskExecution
}
