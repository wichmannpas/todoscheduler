import Vue from 'vue'

import { Day } from '@/models/Day'
import { objectToTask } from '@/models/Task'
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
    taskExecutionToExchange (state) {
      return (execution, direction) => {
        let dayString = formatDayString(execution.day)
        let storedDay = state.days[dayString]
        if (storedDay === undefined) {
          return null
        }

        let exchange = null
        for (let i = 0; i < storedDay.taskExecutions.length; i++) {
          let other = storedDay.taskExecutions[i]

          if (other.finished !== execution.finished) {
            continue
          }

          if (exchange !== null &&
              direction * exchange.dayOrder < direction * other.dayOrder) {
            break
          }

          if (direction * other.dayOrder > direction * execution.dayOrder) {
            exchange = other
          }
        }
        return exchange
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
     * Delete a task execution.
     *
     * Iterate through all days to ensure it is deleted
     * from a previous day if the day has been changed.
     *
     * Furthermore, delete it from missed.
     */
    deleteTaskExecution (context, execution) {
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

      // missed
      for (let i = 0; i < context.state.missed.length; i++) {
        let other = context.state.missed[i]
        if (other.id === execution.id) {
          Vue.delete(context.state.missed, i)
          break
        }
      }
    },
    /**
     * Update a task in all executions that reference it.
     */
    updateTaskInExecutions (context, payload) {
      let task = objectToTask(payload)

      // days
      for (let dayString in context.state.days) {
        if (!context.state.days.hasOwnProperty(dayString)) {
          continue
        }
        let day = context.state.days[dayString]

        for (let i = 0; i < day.taskExecutions.length; i++) {
          let execution = day.taskExecutions[i]

          if (execution.task.id === task.id) {
            Vue.set(execution, 'task', task)
          }
        }
      }

      // missed
      for (let i = 0; i < context.state.missed.length; i++) {
        let execution = context.state.missed[i]
        if (execution.task.id === task.id) {
          Vue.set(execution, 'task', task)
          break
        }
      }
    },
    updateTaskExecution (context, payload) {
      let execution = objectToTaskExecution(payload)

      context.dispatch('deleteTaskExecution', execution)

      // days
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
      if (!execution.finished && execution.past()) {
        context.commit('addMissedTaskExecution', execution)
      }
    }
  }
}
