import { Task } from '@/models/Task'

export default {
  state: {
    incomplete: []
  },
  mutations: {
    addIncompleteTask (state, task) {
      state.incomplete.push(new Task(
        task.id,
        task.name,
        task.duration,
        task.incomplete_duration,
        task.scheduled_duration,
        task.finished_duration,
        task.default_schedule_duration))
    },
    setIncompleteTasks (state, tasks) {
      state.incomplete = []
      for (let i = 0; i < tasks.length; i++) {
        let task = tasks[i]
        state.incomplete.push(new Task(
          task.id,
          task.name,
          task.duration,
          task.incomplete_duration,
          task.scheduled_duration,
          task.finished_duration,
          task.default_schedule_duration))
      }
    }
  }
}
