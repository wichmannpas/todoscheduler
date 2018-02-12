<template>
  <li>
    {{ task.name }}
    ({{ task.incompleteDuration.toNumber() }}h)

    <ScheduleTaskModal
        @close="modalActive = false"
        v-if="modalActive"
        v-bind:task="task"
    />

    <a class="task-edit tooltip"
        data-tooltip="Edit task">
      <span class="fa fa-pencil"></span></a>
    <a
        @click="modalActive = true"
        class="task-schedule tooltip"
        data-tooltip="Schedule">
      <span class="fa fa-play"></span></a>
  </li>
</template>

<script>
import ScheduleTaskModal from '@/components/ScheduleTaskModal'

export default {
  name: 'IncompleteTask',
  props: [
    'task'
  ],
  data: function () {
    return {
      modalActive: false
    }
  },
  components: {
    ScheduleTaskModal
  }
}
</script>
