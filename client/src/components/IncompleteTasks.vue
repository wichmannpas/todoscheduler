<template>
  <div>
    <div v-if="incompleteTasks.length > 0">
      <p>
        Some tasks are not fully scheduled yet!
      </p>
      <ul>
        <IncompleteTask
          v-for="task in incompleteTasks"
          v-bind:key="task.id"
          v-bind:task="task" />
      </ul>
    </div>
  </div>
</template>

<script>
import Api from '@/api/Api'
import IncompleteTask from '@/components/IncompleteTask'

export default {
  name: 'IncompleteTasks',
  components: {
    IncompleteTask
  },
  created: function () {
    Api.getIncompleteTasks(this.$store)
  },
  computed: {
    incompleteTasks () {
      return this.$store.state.tasks.incomplete
    }
  }
}
</script>
