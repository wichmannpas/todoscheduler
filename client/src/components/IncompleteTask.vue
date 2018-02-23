<template>
  <li>
    {{ task.name }}
    ({{ task.incompleteDuration().toNumber() }}h)

    <EditTaskModal
        @close="editModalActive = false"
        v-if="editModalActive"
        v-bind:task="task"
    />

    <ScheduleTaskModal
        @close="scheduleModalActive = false"
        v-if="scheduleModalActive"
        v-bind:task="task"
    />

    <a class="task-edit tooltip"
        @click="editModalActive = true"
        data-tooltip="Edit task">
      <span class="fa fa-pencil"></span></a>
    <a
        @click="finishTask()"
        class="tooltip"
        data-tooltip="Finish task">
      <span class="fa fa-check"></span></a>
    <a
        @click="scheduleModalActive = true"
        class="task-schedule tooltip"
        data-tooltip="Schedule">
      <span class="fa fa-play"></span></a>
  </li>
</template>

<script>
import Api from '@/api/Api'
import EditTaskModal from '@/components/EditTaskModal'
import ScheduleTaskModal from '@/components/ScheduleTaskModal'

export default {
  name: 'IncompleteTask',
  props: [
    'task'
  ],
  data: function () {
    return {
      editModalActive: false,
      scheduleModalActive: false
    }
  },
  components: {
    EditTaskModal,
    ScheduleTaskModal
  },
  methods: {
    finishTask () {
      Api.finishTask(this.$store, this.task)
    }
  }
}
</script>
