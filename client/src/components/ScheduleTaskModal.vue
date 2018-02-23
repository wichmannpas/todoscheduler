<template>
  <div class="modal modal-sm active">
    <div
        @click="closeModal"
        class="modal-overlay">
    </div>
    <div class="modal-container">
      <div class="modal-header">
        <button
            @click="closeModal"
            class="
              btn btn-clear
              float-right">
        </button>
        <div class="modal-title h5">
          Schedule Task
        </div>
      </div>
      <div class="modal-body">
        <div class="columns">
          <div class="column col-6">
            <strong>
              Task Name
            </strong>
          </div>
          <div class="column col-6">
            {{ task.name }}
          </div>
          <div class="column col-6">
            <strong>
              Incomplete Duration
            </strong>
          </div>
          <div class="column col-6">
            <p class="align-right">
              {{ task.incompleteDuration().toNumber() }}h
            </p>
          </div>
        </div>

        <div class="content">
          <ScheduleTaskForm
            @complete="closeModal"
            v-bind:task="task" />
        </div>
        <div class="modal-footer">
          <input
              @click="scheduleTask()"
              type="submit"
              class="btn btn-primary"
              value="Schedule" />
          <button
              @click="closeModal"
              type="reset"
              class="btn btn-link">
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ScheduleTaskForm from '@/components/ScheduleTaskForm'

export default {
  name: 'ScheduleTaskModal',
  props: [
    'task'
  ],
  components: {
    ScheduleTaskForm
  },
  methods: {
    scheduleTask () {
      this.$emit('schedule')
    },
    closeModal () {
      this.$emit('close')
    }
  }
}
</script>
