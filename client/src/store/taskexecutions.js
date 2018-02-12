import Vue from 'vue'

import { Day } from '@/models/Day'
import { objectToTask } from '@/models/Task'
import { objectToTaskExecution } from '@/models/TaskExecution'
import { formatDayString, parseDayString } from '@/utils'

/**
 * Determine the index at which to insert a new task execution
 */
function taskExecutionIndex (taskExecutionList, newTaskExecution) {
  let index = 0
  for (let i = 0; i < taskExecutionList.length; i++) {
    let execution = taskExecutionList[i]

    if (newTaskExecution.finished && !execution.finished) {
      break
    }
    if ((!execution.finished || newTaskExecution.finished) &&
        execution.dayOrder > newTaskExecution.dayOrder) {
      break
    }

    index++
  }

  return index
}

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
    /**
     * Delete a task execution.
     *
     * Iterate through all days to ensure it is deleted
     * from a previous day if the day has been changed.
     *
     * Furthermore, delete it from missed.
     */
    deleteTaskExecution (state, execution) {
      // days
      for (let dayString in state.days) {
        if (!state.days.hasOwnProperty(dayString)) {
          continue
        }
        let day = state.days[dayString]

        for (let i = 0; i < day.taskExecutions.length; i++) {
          let other = day.taskExecutions[i]

          if (execution.id === other.id) {
            Vue.delete(day.taskExecutions, i)
          }
        }
      }

      // missed
      for (let i = 0; i < state.missed.length; i++) {
        let other = state.missed[i]
        if (other.id === execution.id) {
          Vue.delete(state.missed, i)
          break
        }
      }
    },
    addTaskExecutionToDay (state, payload) {
      let execution = objectToTaskExecution(payload)

      let dayString = formatDayString(execution.day)
      let day = state.days[dayString]
      if (day === undefined) {
        console.warn(
          'not adding task execution ' + execution.id.toString() +
          ' to store because day ' + dayString + ' is not yet known')
        return
      }

      let index = taskExecutionIndex(day.taskExecutions, execution)
      day.taskExecutions.splice(index, 0, execution)
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
     * Add a task execution to the proper day.
     *
     * If it is in past and not finished, it is added
     * to missed as well.
     */
    addTaskExecution (context, execution) {
      execution = objectToTaskExecution(execution)

      context.commit('addTaskExecutionToDay', execution)

      // missed
      if (execution.missed()) {
        context.commit('addMissedTaskExecution', execution)
      }
    },
    /**
     * Update a task in all executions that reference it.
     */
    updateTaskInExecutions (context, payload) {
      let task = objectToTask(payload)

      // TODO: use commit instead of doing direct modifications

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

      context.commit('deleteTaskExecution', execution)

      // days
      context.commit('addTaskExecutionToDay', execution)

      // missed
      if (execution.missed()) {
        context.commit('addMissedTaskExecution', execution)
      }
    }
  }
}
