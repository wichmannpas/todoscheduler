<template>
  <div
      v-if="missedTaskExecutions.length > 0"
      class="toast toast-warning">
    There are unfinished scheduled tasks for past days!

    <ul>
      <li
          v-for="execution in missedTaskExecutions"
          v-bind:key="execution.id">
          {{ execution.task.name }} ({{ execution.naturalDay() }})
          <a
              @click="finishExecution(execution)"
              class="tooltip"
              data-tooltip="Done">
            <span class="fa fa-check"></span></a>
          <a
              @click="postponeExecution(execution)"
              class="tooltip"
              data-tooltip="Postpone to another day">
            <span class="fa fa-clock-o"></span></a>
      </li>
    </ul>
  </div>
</template>

<script>
import Api from '@/api/Api'

export default {
  name: 'MissedTaskExecutions',
  created: function () {
    Api.getMissedTaskExecutions(this.$store)
  },
  computed: {
    missedTaskExecutions () {
      return this.$store.getters.missedTaskExecutions
    }
  },
  methods: {
    finishExecution (execution) {
      Api.finishTaskExecution(
        this.$store,
        execution,
        true)
    },
    postponeExecution (execution) {
      Api.deleteTaskExecution(
        this.$store,
        execution,
        true)
    }
  }
}
</script>
