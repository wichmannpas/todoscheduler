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
      <form
          @submit="createTask">
        <div class="modal-body">
          <div class="content">

            <input
                ref="name"
                v-model="task.name"
                v-bind:disabled="loading"
                v-bind:class="[
                  { 'is-error': errors.indexOf('name') >= 0 }
                ]"
                type="text"
                class="form-input"
                placeholder="Name"
                maxlength="40" />

            <div class="input-group">
              <input
                  v-model="task.duration"
                  v-bind:disabled="loading"
                  v-bind:class="[
                    { 'is-error': errors.indexOf('duration') >= 0 }
                  ]"
                  type="number"
                  class="
                    form-input
                    align-right"
                  placeholder="Duration"
                  step="0.01" />
              <span class="input-group-addon">h</span>
            </div>

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
          <input
              v-bind:disabled="loading"
              type="submit"
              class="btn btn-primary"
              value="Create Task"/>
          <button
              @click="closeModal"
              type="reset"
              class="
                btn btn-link">
            Cancel
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import Vue from 'vue'

import Api from '@/api/Api'
import { objectToTask } from '@/models/Task'

export default {
  name: 'NewTaskModal',
  data: function () {
    return {
      loading: false,
      schedule: false,
      scheduleFor: 'today',
      errors: [],
      task: {
        name: '',
        duration: 1
      }
    }
  },
  mounted: function () {
    this.$refs.name.focus()
  },
  methods: {
    createTask (event) {
      event.preventDefault()
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
