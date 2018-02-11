import Vue from 'vue'

import { objectToTask } from '@/models/Task'

export default {
  state: {
    incomplete: []
  },
  mutations: {
    addIncompleteTask (state, task) {
      state.incomplete.push(objectToTask(task))
    },
    setIncompleteTasks (state, tasks) {
      state.incomplete = []
      for (let i = 0; i < tasks.length; i++) {
        let task = tasks[i]
        state.incomplete.push(objectToTask(task))
      }
    },
    /**
     * Update a task at all occurences
     */
    updateTask (state, payload) {
      let task = objectToTask(payload)

      for (let i = 0; i < state.incomplete.length; i++) {
        let otherTask = state.incomplete[i]

        if (otherTask.id === task.id) {
          Vue.set(state.incomplete, i, task)
        }
      }
    }
  }
}
