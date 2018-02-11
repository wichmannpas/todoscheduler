import Vue from 'vue'

import { Day } from '@/models/Day'
import { objectToTaskExecution } from '@/models/TaskExecution'
import { formatDayString, parseDayString } from '@/utils'

export default {
  state: {
    days: {},
    missed: []
  },
  getters: {
    taskExecutionsForDay (state) {
      return day => {
        let dayString = formatDayString(day)
        let storedDay = state.days[dayString]
        let executions = []
        let maxDuration = 0
        if (storedDay !== undefined) {
          return storedDay
        }

        // not stored, empty day
        console.warn('day ' + dayString + ' not in store')
        return new Day(
          day,
          maxDuration,
          executions)
      }
    },
    missedTaskExecutions (state) {
      return state.missed
    }
  },
  mutations: {
    setTaskExecutionsForDay (state, payload) {
      let executions = []
      for (let i = 0; i < payload.executions.length; i++) {
        let execution = payload.executions[i]
        executions.push(objectToTaskExecution(execution))
      }

      let day = new Day(
        parseDayString(payload.day),
        payload.max_duration,
        executions)

      Vue.set(state.days, payload.day, day)
    },
    addMissedTaskExecution (state, payload) {
      state.missed.push(payload)
    },
    setMissedTaskExecutions (state, payload) {
      state.missed = []
      for (let i = 0; i < payload.length; i++) {
        let execution = payload[i]
        state.missed.push(objectToTaskExecution(execution))
      }
    }
  },
  actions: {
    /**
     * Update a task execution.
     *
     * Iterate through all days to ensure it is deleted
     * from a previous day if the day has been changed.
     *
     * Furthermore, missed is updated.
     */
    updateTaskExecution (context, payload) {
      let execution = objectToTaskExecution(payload)

      // days
      for (let dayString in context.state.days) {
        if (!context.state.days.hasOwnProperty(dayString)) {
          continue
        }
        let day = context.state.days[dayString]

        for (let i = 0; i < day.taskExecutions.length; i++) {
          let other = day.taskExecutions[i]

          if (execution.id === other.id) {
            Vue.delete(day.taskExecutions, i)
          }
        }
      }
      let day = context.state.days[formatDayString(execution.day)]
      // determine at which index to put this execution
      let index = 0
      for (let i = 0; i < day.taskExecutions.length; i++) {
        let other = day.taskExecutions[i]

        if (execution.finished && !other.finished) {
          break
        }
        if ((!other.finished || execution.finished) &&
            other.dayOrder > execution.dayOrder) {
          break
        }

        index++
      }
      day.taskExecutions.splice(index, 0, execution)

      // missed
      let contained = false
      for (let i = 0; i < context.state.missed.length; i++) {
        let other = context.state.missed[i]
        if (other.id === execution.id) {
          contained = true
          if (execution.finished) {
            Vue.delete(context.state.missed, i)
          } else {
            Vue.set(context.state.missed, i, execution)
          }
          break
        }
      }
      if (!contained && !execution.finished && execution.past()) {
        context.commit('addMissedTaskExecution', execution)
      }
    }
  }
}
