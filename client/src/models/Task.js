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

export {
  Task
}
