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
    }
  }
}
