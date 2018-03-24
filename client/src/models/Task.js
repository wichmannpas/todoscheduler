import { isAfter } from 'date-fns'
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
Task.prototype.startInFuture = function () {
  let today = new Date()

  return isAfter(this.start, today)
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

/**
 * Compare tasks a and b.
 * returns negative values if a < b
 * 0 if a = b
 * positive values if a > b
 */
function compareTasks (a, b) {
  // first criterion: start
  if (a.start === null && b.start !== null) {
    return -1
  } else if (a.start !== null && b.start === null) {
    return 1
  } else if (a.start < b.start) {
    return -1
  } else if (a.start > b.start) {
    return 1
  }
  // start equals, use second criterion

  // second criterion: name
  return a.name > b.name
}

export {
  compareTasks,
  objectToTask,
  Task
}
