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
          New Task
        </div>
      </div>
      <div class="modal-body">
        <div class="content">
          <TaskForm
              @submit="createTask"
              v-model="task"
              v-bind:autofocus="true"
              v-bind:loading="loading"
              v-bind:errors="errors"
          />

          <div class="form-group">
            <label class="form-switch">
              <input
                  v-model="schedule"
                  v-bind:disabled="loading"
                  type="checkbox">
              <i class="form-icon"></i> Schedule
            </label>
          </div>
          <select
              v-model="scheduleFor"
              v-if="schedule"
              class="form-select">
            <option value="today">Today</option>
            <option value="tomorrow">Tomorrow</option>
          </select>

          <div
              v-if="loading"
              class="loading loading-lg">
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button
            @click="createTask"
            v-bind:disabled="loading"
            class="btn btn-primary">
          Create Task
        </button>
        <button
            @click="closeModal"
            type="reset"
            class="
              btn btn-link">
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import Vue from 'vue'

import Api from '@/api/Api'
import { objectToTask } from '@/models/Task'
import TaskForm from '@/components/TaskForm'

export default {
  name: 'NewTaskModal',
  components: {
    TaskForm
  },
  data: function () {
    return {
      loading: false,
      schedule: false,
      scheduleFor: 'today',
      errors: [],
      task: {
        name: '',
        duration: 1,
        start: null
      }
    }
  },
  methods: {
    createTask () {
      this.loading = true

      Api.createTask(this.$store, this.task).then((task) => {
        if (this.schedule) {
          Api.scheduleTask(
            this.$store,
            objectToTask(task),
            this.scheduleFor,
            this.task.duration
          ).then((response) => {
            this.loading = false
            Vue.set(this, 'errors', [])

            this.closeModal()
          }).catch((response) => {
            this.loading = false

            Vue.set(this, 'errors', Object.keys(response))
          })
        } else {
          this.loading = false
          Vue.set(this, 'errors', [])

          this.closeModal()
        }
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
