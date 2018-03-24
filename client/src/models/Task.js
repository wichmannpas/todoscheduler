import { Decimal } from 'decimal.js'
import { parseDayString } from '@/utils'

function Task (id, name, duration, scheduledDuration, finishedDuration, defaultScheduleDuration, start) {
  this.id = id
  this.name = name
  this.duration = Decimal(duration)
  this.scheduledDuration = Decimal(scheduledDuration)
  this.finishedDuration = Decimal(finishedDuration)
  this.defaultScheduleDuration = Decimal(defaultScheduleDuration)
  this.start = start
  if (start !== null) {
    this.start = parseDayString(start)
  }
}
Task.prototype.incompleteDuration = function () {
  return this.duration.sub(this.scheduledDuration)
}
Task.prototype.incomplete = function () {
  return this.incompleteDuration().toNumber() > 0
}

function objectToTask (task) {
  if (task instanceof Task) {
    return task
  }
  return new Task(
    task.id,
    task.name,
    task.duration,
    task.scheduled_duration,
    task.finished_duration,
    task.default_schedule_duration,
    task.start)
}

export {
  objectToTask,
  Task
}
