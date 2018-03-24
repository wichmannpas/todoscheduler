<template>
  <div>
    <div
        v-if="incompleteTasks.length > 0"
        style="
          max-height: 12em;
          overflow-x: hidden;
          overflow-y: auto;">
      <div class="columns">
        <div class="column col-6 col-sm-12">
          <ul>
            <IncompleteTask
              v-for="task in activeTasks"
              v-bind:key="task.id"
              v-bind:task="task" />
          </ul>
        </div>
        <div class="column col-6 col-sm-12">
          <div class="accordion">
            <input type="checkbox" id="accordion-futureTasks" name="accordion-checkbox" hidden>
            <label class="accordion-header c-hand" for="accordion-futureTasks">
              <strong>
                Future Tasks
              </strong>
            </label>
            <div class="accordion-body">
              <ul>
                <IncompleteTask
                  v-for="task in futureTasks"
                  v-bind:key="task.id"
                  v-bind:task="task" />
              </ul>
            </div>
          </div>
        </div>
      </div>
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
    },
    activeTasks () {
      return this.$store.state.tasks.incomplete.filter(
        task => !task.startInFuture())
    },
    futureTasks () {
      return this.$store.state.tasks.incomplete.filter(
        task => task.startInFuture())
    }
  }
}
</script>
