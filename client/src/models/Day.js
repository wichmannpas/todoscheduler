import { isToday } from 'date-fns'
import { Decimal } from 'decimal.js'

import { formatDayString, isPastDay, naturalDay } from '@/utils.js'

function Day (day, maxDuration, taskExecutions) {
  this.day = day
  this.dayString = formatDayString(day)
  maxDuration = Decimal(maxDuration)
  this.maxDuration = () => maxDuration
  this.taskExecutions = taskExecutions
}
Day.prototype.scheduledDuration = function () {
  return aggregateTaskExecutionDuration(this.taskExecutions)
}
Day.prototype.finishedDuration = function () {
  return aggregateTaskExecutionDuration(
    this.taskExecutions.filter(
      item => item.finished))
}
Day.prototype.remainingDuration = function () {
  return this.scheduledDuration().sub(this.finishedDuration())
}
Day.prototype.overloaded = function () {
  return this.scheduledDuration().toNumber() > this.maxDuration().toNumber()
}
Day.prototype.naturalDay = function () {
  return naturalDay(this.day)
}
Day.prototype.past = function () {
  return isPastDay(this.day)
}
Day.prototype.today = function () {
  return isToday(this.day)
}

function aggregateTaskExecutionDuration (taskExecutions) {
  let result = Decimal(0)
  for (let i = 0; i < taskExecutions.length; i++) {
    result = result.add(taskExecutions[i].duration)
  }
  return result
}

export {
  Day
}
