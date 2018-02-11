<template>
  <div>
    <div v-if="incompleteTasks.length > 0">
      <p>
        Some tasks are not fully scheduled yet!
      </p>
      <ul>
        <li v-for="task in incompleteTasks" v-bind:key="task.id">
          {{ task.name }}
          ({{ task.incompleteDuration.toNumber() }}h)

          <a class="task-edit tooltip"
              data-tooltip="Edit task">
            <span class="fa fa-pencil"></span></a>
          <a class="task-schedule tooltip"
              data-tooltip="Schedule">
            <span class="fa fa-play"></span></a>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import Api from '@/api/Api'

export default {
  created: function () {
    Api.getIncompleteTasks(this.$store)
  },
  computed: {
    incompleteTasks () {
      return this.$store.state.tasks.incomplete
    }
  }
}
</script>
