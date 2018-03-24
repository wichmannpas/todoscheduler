import Vue from 'vue'

import { compareTasks, objectToTask } from '@/models/Task'

/**
 * Find the index at which to insert a new task.
 */
function taskIndex (taskList, newTask) {
  let index = 0
  while (index < taskList.length) {
    let task = taskList[index]

    if (compareTasks(task, newTask) > 0) {
      break
    }

    index++
  }

  return index
}

export default {
  state: {
    incomplete: []
  },
  mutations: {
    addIncompleteTask (state, task) {
      let index = taskIndex(state.incomplete, task)

      state.incomplete.splice(index, 0, objectToTask(task))
    },
    clearIncompleteTasks (state) {
      Vue.set(state, 'incomplete', [])
    },
    deleteIncompleteTask (state, payload) {
      let task = objectToTask(payload)

      for (let i = 0; i < state.incomplete.length; i++) {
        let otherTask = state.incomplete[i]

        if (otherTask.id === task.id) {
          Vue.delete(state.incomplete, i)
        }
      }
    }
  },
  actions: {
    setIncompleteTasks (context, tasks) {
      context.commit('clearIncompleteTasks')
      for (let i = 0; i < tasks.length; i++) {
        let task = tasks[i]
        context.commit('addIncompleteTask', objectToTask(task))
      }
    },
    updateTask (context, payload) {
      let task = objectToTask(payload)

      context.commit('deleteIncompleteTask', task)

      if (task.incomplete()) {
        context.commit('addIncompleteTask', task)
      }
    }
  }
}
