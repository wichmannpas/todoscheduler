<template>
  <span
      v-bind:class="[
        'task-execution',
        { finished: execution.finished },
        { overdue: execution.overdue }
      ]"
      v-bind:style="[
        { height: (execution.duration.toNumber() * 4).toString() + 'em' }
      ]">
    <strong>{{ execution.task.name }}</strong>
    <span
      v-if="loading"
      class="loading loading-lg"></span>
    <span class="float-right">
      {{ execution.duration.toNumber() }}h
      <span v-if="execution.task.duration.toNumber() !== execution.duration.toNumber()">
        ({{ execution.task.duration.toNumber() }}h)
      </span>
    </span>
    <br/>
    <span class="float-left">
      <a
          @click="finishExecution(true)"
          v-if="!execution.finished"
          class="tooltip tooltip-right"
          data-tooltip="Done">
        <span class="fa fa-check"></span>
      </a>
      <a
          @click="finishExecution(false)"
          v-if="execution.finished"
          class="tooltip tooltip-right"
          data-tooltip="Not done">
        <span class="fa fa-undo"></span>
      </a>
      <a
          @click="deleteExecution()"
          class="tooltip tooltip-right"
          data-tooltip="No time needed on this day">
        <span class="fa fa-times"></span>
      </a>
      <a
          @click="postponeExecution()"
          class="tooltip tooltip-right"
          data-tooltip="Postpone to another day">
        <span class="fa fa-clock-o"></span>
      </a>
      <a
          @click="increaseTaskDuration(1)"
          class="tooltip tooltip-right"
          data-tooltip="Needs more time on another day">
        <span class="fa fa-files-o"></span>
      </a>
      <a
          @click="editTask()"
          class="
            task-edit
            tooltip tooltip-right"
          data-tooltip="Edit task">
        <span class="fa fa-pencil"></span></a>
    </span>
    <span class="float-right">
      <a
          @click="moveExecution(-1)"
          class="tooltip tooltip-left"
          v-bind:class="[
            { 'invisible': execution.finished }
          ]"
         data-tooltip="Needs time earlier">
        <span class="fa fa-arrow-up"></span>
      </a>
      <a
          @click="moveExecution(1)"
          class="tooltip tooltip-left invisible{% endif %}"
          v-bind:class="[
            { 'invisible': execution.finished }
          ]"
          data-tooltip="Needs time later">
        <span class="fa fa-arrow-down"></span>
      </a>
      <a
          @click="changeExecutionDuration(-0.5)"
          class="tooltip tooltip-left"
          v-bind:class="[
            { 'invisible': execution.duration <= 0.5 }
          ]"
          data-tooltip="Takes 30 less minutes">
        <span class="fa fa-minus"></span>
      </a>
      <a
          @click="changeExecutionDuration(-0.5)"
          class="tooltip tooltip-left"
          data-tooltip="Takes 30 more minutes">
        <span class="fa fa-plus"></span>
      </a>
    </span>
  </span>
</template>

<script>
import Api from '@/api/Api'

export default {
  name: 'TaskExecution',
  props: [
    'execution'
  ],
  data: function () {
    return {
      loading: false
    }
  },
  methods: {
    changeExecutionDuration (delta) {
      console.log('updating')
    },
    deleteExecution () {
      if (!confirm('Are you sure that you want to delete this task execution?')) {
        return
      }

      console.log('delete')
    },
    editTask () {
      console.log('edit task')
    },
    finishExecution (newState) {
      this.loading = true
      Api.finishTaskExecution(
        this.$store,
        this.execution,
        newState).then(
        () => {
          this.loading = false
        })
    },
    increaseTaskDuration (delta) {
      console.log('increase task')
    },
    moveExecution (delta) {
    },
    postponeExecution () {
      console.log('postponing')
    }
  }
}
</script>
