import { Decimal } from 'decimal.js'

function Task (id, name, duration, scheduledDuration, finishedDuration, defaultScheduleDuration) {
  this.id = id
  this.name = name
  this.duration = Decimal(duration)
  this.scheduledDuration = Decimal(scheduledDuration)
  this.finishedDuration = Decimal(finishedDuration)
  this.defaultScheduleDuration = Decimal(defaultScheduleDuration)
}
Task.prototype.incompleteDuration = function () {
  return this.duration.sub(this.scheduledDuration)
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
    task.default_schedule_duration)
}

export {
  objectToTask,
  Task
}
