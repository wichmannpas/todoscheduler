import Vue from 'vue'

import { format } from 'date-fns'
import { Day } from '@/models/Day'
import { Task } from '@/models/Task'
import { TaskExecution } from '@/models/TaskExecution'

export default {
  state: {
    days: {},
    missed: []
  },
  getters: {
    taskExecutionsForDay (state) {
      return day => {
        // TODO: explicitly order the executions

        let dayString = format(day, 'YYYY-MM-DD')
        let storedDay = state.days[dayString]
        let executions = []
        let maxDuration = 0
        if (storedDay !== undefined) {
          executions = storedDay.executions
          maxDuration = storedDay.max_duration
        }

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
        executions.push(new TaskExecution(
          execution.id,
          new Task(
            execution.task.id,
            execution.task.name,
            execution.task.duration,
            execution.task.incomplete_duration,
            execution.task.scheduled_duration,
            execution.task.finished_duration,
            execution.task.default_schedule_duration),
          execution.day,
          execution.day_order,
          execution.duration,
          execution.finished
        ))
      }
      payload.executions = executions
      Vue.set(state.days, payload.day, payload)
    },
    setMissedTaskExecutions (state, payload) {
      state.missed = []
      for (let i = 0; i < payload.length; i++) {
        let execution = payload[i]
        state.missed.push(new TaskExecution(
          execution.id,
          new Task(
            execution.task.id,
            execution.task.name,
            execution.task.duration,
            execution.task.incomplete_duration,
            execution.task.scheduled_duration,
            execution.task.finished_duration,
            execution.task.default_schedule_duration),
          execution.day,
          execution.day_order,
          execution.duration,
          execution.finished
        ))
      }
    }
  }
}
