
<template>
    <div class="employee-dashboard">
        <!-- Employee toolbar -->
        <EmployeeToolbar />

        <ProjectStatusCards />

        <!-- Projects, tasks and complaints -->
        <div class="dashboard-workspace">
            <ProjectWorkspace />
            <NotificationsTodo />
        </div>
    </div>
</template>

<script setup>
import EmployeeToolbar from '../components/EmployeeToolbar.vue'
import ProjectStatusCards from '../components/ProjectStatusCards.vue'
import ProjectWorkspace from '../components/ProjectWorkspace.vue'
import NotificationsTodo from '../components/NotificationsTodo.vue'</script>

<style scoped>
.employee-dashboard {
    width: 100%;
    min-height: 100%;
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

/* Preserve the Employee Toolbar's existing position */
.employee-dashboard > :first-child {
    margin-bottom: 30px;
}

/* Align all remaining sections with the Employee Toolbar */
.employee-dashboard > :not(:first-child) {
    margin-left: 16px;
    width: calc(100% - 32px);
    box-sizing: border-box;
}

/* Dashboard workspace */
.dashboard-workspace {
    position: relative;
    display: grid;
    grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
    gap: 16px;
    padding-bottom: 20px;
}

@media (max-width: 1100px) {
    .dashboard-workspace {
        grid-template-columns: minmax(0, 1fr);
    }
}
</style>
