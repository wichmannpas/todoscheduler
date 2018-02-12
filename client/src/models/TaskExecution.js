import { Decimal } from 'decimal.js'

import { objectToTask } from '@/models/Task'
import { isPastDay, naturalDay } from '@/utils'

function TaskExecution (id, task, day, dayOrder, duration, finished) {
  this.id = id
  this.task = task
  this.day = day
  this.dayOrder = dayOrder
  this.duration = Decimal(duration)
  this.finished = finished
}
TaskExecution.prototype.past = function () {
  return isPastDay(this.day)
}
TaskExecution.prototype.missed = function () {
  return !this.finished && this.past()
}
TaskExecution.prototype.naturalDay = function () {
  return naturalDay(this.day)
}

function objectToTaskExecution (execution) {
  if (execution instanceof TaskExecution) {
    return execution
  }
  return new TaskExecution(
    execution.id,
    objectToTask(execution.task),
    execution.day,
    execution.day_order,
    execution.duration,
    execution.finished)
}

export {
  objectToTaskExecution,
  TaskExecution
}
