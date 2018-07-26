import { differenceInDays, format, isPast, isToday, isTomorrow, isYesterday, parse } from 'date-fns'

function formatDayString (day) {
  return format(day, 'YYYY-MM-DD')
}

function parseDayString (day) {
  return parse(day)
}

function naturalDay (day) {
  if (isYesterday(day)) {
    return 'yesterday'
  } else if (isToday(day)) {
    return 'today'
  } else if (isTomorrow(day)) {
    return 'tomorrow'
  }

  let today = new Date()
  if (differenceInDays(today, day) <= 7) {
    return format(day, 'dddd')
  }
  return format(day, 'MMM. D, YYYY')
}

function isPastDay (day) {
  return isPast(new Date(format(day, 'YYYY-MM-DD') + 'T23:59:59'))
}

/**
 * Add the delta (in microseconds) to the string-formatted day.
 */
function dayDelta (day, delta) {
  let newDay = new Date(new Date(day).getTime() + delta)
  return formatDayString(newDay)
}

export {
  dayDelta,
  formatDayString,
  parseDayString,
  isPastDay,
  naturalDay
}
