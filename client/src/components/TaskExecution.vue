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
          @click="editModalActive = true"
          class="
            task-edit
            tooltip tooltip-right"
          data-tooltip="Edit task">
        <span class="fa fa-pencil"></span></a>
    </span>
    <span class="float-right">
      <a
          @click="updateExecutionDay(-1)"
          class="tooltip tooltip-left"
          v-bind:class="[
            { 'invisible': execution.finished }
          ]"
          data-tooltip="Move to previous day">
        <span class="fa fa-arrow-left"></span>
      </a>
      <a
          @click="moveExecution(-1)"
          class="tooltip tooltip-left"
          v-bind:class="[
            { 'invisible': execution.finished },
            { 'invisible': !canBeMovedUp }
          ]"
         data-tooltip="Needs time earlier">
        <span class="fa fa-arrow-up"></span>
      </a>
      <a
          @click="moveExecution(1)"
          class="tooltip tooltip-left"
          v-bind:class="[
            { 'invisible': execution.finished },
            { 'invisible': !canBeMovedDown }
          ]"
          data-tooltip="Needs time later">
        <span class="fa fa-arrow-down"></span>
      </a>
      <a
          @click="updateExecutionDay(1)"
          class="tooltip tooltip-left"
          v-bind:class="[
            { 'invisible': execution.finished }
          ]"
          data-tooltip="Move to next day">
        <span class="fa fa-arrow-right"></span>
      </a>
      <a
          @click="changeExecutionDuration('-0.5')"
          class="tooltip tooltip-left"
          v-bind:class="[
            { 'invisible': execution.duration.toNumber() <= 0.5 }
          ]"
          data-tooltip="Takes 30 less minutes">
        <span class="fa fa-minus"></span>
      </a>
      <a
          @click="changeExecutionDuration('0.5')"
          class="tooltip tooltip-left"
          data-tooltip="Takes 30 more minutes">
        <span class="fa fa-plus"></span>
      </a>
    </span>
    <EditTaskModal
        @close="editModalActive = false"
        v-if="editModalActive"
        v-bind:task="execution.task"
    />
  </span>
</template>

<script>
import Api from '@/api/Api'
import EditTaskModal from '@/components/EditTaskModal'
import { dayDelta } from '@/utils'

export default {
  name: 'TaskExecution',
  components: {
    EditTaskModal
  },
  props: [
    'execution'
  ],
  data: function () {
    return {
      loading: false,
      editModalActive: false
    }
  },
  computed: {
    canBeMovedUp () {
      return this.$store.getters.taskExecutionToExchange(
        this.execution, -1) !== null
    },
    canBeMovedDown () {
      return this.$store.getters.taskExecutionToExchange(
        this.execution, 1) !== null
    }
  },
  methods: {
    changeExecutionDuration (delta) {
      this.loading = true
      Api.changeTaskExecutionDuration(
        this.$store,
        this.execution,
        this.execution.duration.add(delta).toString()).then(
        () => {
          this.loading = false
        })
    },
    deleteExecution () {
      if (!confirm('Are you sure that you want to delete this task execution?')) {
        return
      }

      this.loading = true
      Api.deleteTaskExecution(
        this.$store,
        this.execution,
        false).then(
        () => {
          this.loading = false
        })
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
      this.loading = true
      Api.changeTaskDuration(
        this.$store,
        this.execution.task,
        this.execution.task.duration.add(delta.toString())).then(
        () => {
          this.loading = false
        })
    },
    moveExecution (direction) {
      let exchange = this.$store.getters.taskExecutionToExchange(
        this.execution,
        direction)
      if (exchange === null) {
        // nothing to exchange with
        return
      }

      this.loading = true
      Api.exchangeTaskExecution(
        this.$store,
        this.execution,
        exchange).then(
        () => {
          this.loading = false
        })
    },
    postponeExecution () {
      this.loading = true
      Api.deleteTaskExecution(
        this.$store,
        this.execution,
        true).then(
        () => {
          this.loading = false
        })
    },
    updateExecutionDay (direction) {
      let newDay = dayDelta(
        this.execution.day,
        direction * 86400000)
      console.log(this.execution.day)

      this.loading = true
      Api.updateTaskExecutionDay(
        this.$store,
        this.execution,
        newDay).then(
        () => {
          this.loading = false
        })
    }
  }
}
</script>
