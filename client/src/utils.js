import { differenceInDays, format, isToday, isTomorrow, isYesterday } from 'date-fns'

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

export {
  naturalDay
}
