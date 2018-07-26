<template>
  <form
      @submit.prevent="$emit('submit')">
    <input
        ref="name"
        :value="value.name"
        @input="updateTask"
        @keyup.enter="$emit('submit')"
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
          ref="duration"
          :value="value.duration"
          @input="updateTask"
          @keyup.enter="$emit('submit')"
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

    <input
        ref="start"
        :value="startString"
        @input="updateTask"
        @keyup.enter="$emit('submit')"
        v-bind:disabled="loading"
        v-bind:class="[
          { 'is-error': errors.indexOf('start') >= 0 }
        ]"
        type="date"
        class="form-input"
        placeholder="Start" />
  </form>
</template>

<script>
import { formatDayString } from '@/utils'

export default {
  name: 'TaskForm',
  props: [
    'value',
    'loading',
    'errors',
    'autofocus'
  ],
  mounted: function () {
    if (this.autofocus) {
      this.$refs.name.focus()
    }
  },
  computed: {
    startString () {
      if (this.value.start === null) {
        return null
      }
      return formatDayString(this.value.start)
    }
  },
  methods: {
    updateTask () {
      let start = this.$refs.start.value
      if (start === '') {
        start = null
      }
      this.$emit('input', {
        name: this.$refs.name.value,
        duration: this.$refs.duration.value,
        start: start
      })
    }
  }
}
</script>
