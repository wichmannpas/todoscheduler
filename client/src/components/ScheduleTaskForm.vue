<template>
  <form
      @submit.prevent="scheduleTask">
    <div class="form-group">
      <label class="form-label">
        Schedule for
      </label>
      <select
          v-model="scheduleFor"
          v-bind:class="[
            { 'is-error': errors.indexOf('day') >= 0 }
          ]"
          class="form-select">
        <option value="today">Today</option>
        <option value="tomorrow">Tomorrow</option>
        <option value="next_free_capacity">Next Free Capacity</option>
        <option value="another_time">Another Time</option>
      </select>
      <input
          @keyup.enter="scheduleTask"
          v-model="scheduleForDate"
          v-bind:class="[
            { 'is-error': errors.indexOf('day') >= 0 }
          ]"
          v-if="scheduleFor === 'another_time'"
          type="date"
          class="form-input"
          placeholder="Schedule for date"
          required />
    </div>
    <div
        class="input-group">
      <input
          ref="duration"
          v-model="duration"
          v-bind:class="[
            { 'is-error': errors.indexOf('duration') >= 0 }
          ]"
          type="number"
          class="
            align-right
            form-input"
            placeholder="Duration"
            step="0.01"
            required />
      <span class="input-group-addon">h</span>

    </div>
    <div
        v-if="loading"
        class="loading loading-lg">
    </div>
  </form>
</template>

<script>
import Vue from 'vue'

import Api from '@/api/Api'
import { formatDayString } from '@/utils'

export default {
  name: 'ScheduleTaskForm',
  props: [
    'task'
  ],
  data: function () {
    return {
      loading: false,
      scheduleFor: 'today',
      scheduleForDate: formatDayString(new Date()),
      duration: this.task.defaultScheduleDuration.toNumber(),
      errors: []
    }
  },
  created: function () {
    this.$parent.$on('schedule', this.scheduleTask)
  },
  mounted: function () {
    this.$refs.duration.focus()
  },
  methods: {
    scheduleTask () {
      if (this.loading) {
        return
      }

      this.loading = true

      let day = this.scheduleForDate
      if (this.scheduleFor !== 'another_time') {
        day = this.scheduleFor
      }
      Api.scheduleTask(this.$store, this.task, day, this.duration).then((response) => {
        this.loading = false
        Vue.set(this, 'errors', [])

        this.$emit('complete')
      }).catch((response) => {
        this.loading = false

        Vue.set(this, 'errors', Object.keys(response))
      })
    }
  }
}
</script>
