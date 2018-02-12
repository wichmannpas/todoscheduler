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
      <form
          @submit="updateTask">
        <div class="modal-body">
          <div class="content">
            <p>
              Scheduled: {{ task.scheduledDuration.toNumber() }}h
              ({{ task.finishedDuration.toNumber() }}h finished)
            </p>

            <input
                v-model="editedTask.name"
                v-bind:class="[
                  { 'is-error': errors.indexOf('name') >= 0 }
                ]"
                type="text"
                class="form-input"
                placeholder="Name" />

            <div class="input-group">
              <input
                  v-model="editedTask.duration"
                  v-bind:class="[
                    { 'is-error': errors.indexOf('duration') >= 0 }
                  ]"
                  type="number"
                  step="0.01"
                  class="form-input"
                  placeholder="Duration" />
              <span class="input-group-addon">h</span>
            </div>
          </div>
          <div
              v-if="loading"
              class="loading loading-lg">
          </div>
        </div>
        <div class="modal-footer">
          <input
              type="submit"
              class="btn btn-primary"
              value="Update Task" />
          <button
              @click="closeModal"
              type="reset"
              class="btn btn-link">
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

export default {
  name: 'EditTaskModal',
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
  mounted: function () {
    // this.$refs.name.focus()
  },
  methods: {
    updateTask (event) {
      event.preventDefault()
      this.loading = true

      Api.updateTask(this.$store, this.editedTask).then((response) => {
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
