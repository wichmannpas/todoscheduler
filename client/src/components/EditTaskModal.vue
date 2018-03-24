<template>
  <div class="modal modal-sm active">
    <div
        @click="closeModal"
        class="modal-overlay"></div>
    <div class="modal-container">
      <div class="modal-header">
        <button
          @click="closeModal"
          class="btn btn-clear float-right modal-close"></button>
        <div class="modal-title h5">
          Edit Task
        </div>
      </div>
      <div class="modal-body">
        <div class="content">
          <p>
            Scheduled: {{ task.scheduledDuration.toNumber() }}h
            ({{ task.finishedDuration.toNumber() }}h finished)
          </p>

          <TaskForm
              @submit="updateTask"
              v-model="editedTask"
              v-bind:autofocus="true"
              v-bind:loading="loading"
              v-bind:errors="errors"
          />
        </div>
        <div
            v-if="loading"
            class="loading loading-lg">
        </div>
      </div>
      <div class="modal-footer">
        <button
            @click="updateTask"
            class="btn btn-primary">
          Update Task
        </button>
        <button
            @click="closeModal"
            type="reset"
            class="btn btn-link">
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import Vue from 'vue'

import Api from '@/api/Api'
import TaskForm from '@/components/TaskForm'

export default {
  name: 'EditTaskModal',
  components: {
    TaskForm
  },
  props: [
    'task'
  ],
  data: function () {
    return {
      loading: false,
      errors: [],
      editedTask: Object.assign({}, this.task)
    }
  },
  methods: {
    updateTask () {
      this.loading = true

      let task = Object.assign({}, this.editedTask)
      task.id = this.task.id
      Api.updateTask(this.$store, task).then((response) => {
        this.loading = false
        Vue.set(this, 'errors', [])

        this.closeModal()
      }).catch((response) => {
        this.loading = false

        Vue.set(this, 'errors', Object.keys(response))
      })
    },
    closeModal () {
      this.$emit('close')
    }
  }
}
</script>
