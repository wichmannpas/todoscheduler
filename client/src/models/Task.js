import { Decimal } from 'decimal.js'

function Task (id, name, duration, incompleteDuration, scheduledDuration, finishedDuration, defaultScheduleDuration) {
  this.id = id
  this.name = name
  this.duration = Decimal(duration)
  this.incompleteDuration = Decimal(incompleteDuration)
  this.scheduledDuration = Decimal(scheduledDuration)
  this.finishedDuration = Decimal(finishedDuration)
  this.defaultScheduleDuration = Decimal(defaultScheduleDuration)
}

function objectToTask (task) {
  return new Task(
    task.id,
    task.name,
    task.duration,
    task.incomplete_duration,
    task.scheduled_duration,
    task.finished_duration,
    task.default_schedule_duration)
}

export {
  objectToTask,
  Task
}
