
<template>
    <div class="project-status-grid">

        <!-- TOTAL PROJECTS -->
        <div class="status-card" data-tour="status-cards">
            <div class="status-card-header">
                <div class="status-heading">
                    <span class="status-icon">
                        <Icon name="lucide-folder-kanban" />
                    </span>
                    <span class="status-label">Total Projects</span>
                </div>
            </div>

            <div class="status-value">
                {{ hasData ? totalProjects : '—' }}
            </div>
        </div>

        <!-- ASSIGNED PROJECTS -->
        <div class="status-card assigned-card" data-tour="assigned-projects">
            <div class="status-card-header">
                <div class="status-heading">
                    <span class="status-icon">
                        <Icon name="lucide-clipboard-list" />
                    </span>
                    <span class="status-label">Assigned Projects</span>
                </div>
            </div>

            <div class="status-value">
                {{ hasData ? assignedProjectsCount : '—' }}
            </div>


            <!-- PROJECT PROGRESS POPUP -->
            <div class="project-progress-popup">

                <div class="popup-header">
                    <span class="popup-title">Project Progress</span>

                    <div class="popup-status-group">
                        <button
                            type="button"
                            class="popup-count all-count"
                            :class="{ active: activeFilter === 'all' }"
                            @click="activeFilter = 'all'"
                        >
                            {{ projects.length }} All
                        </button>

                        <button
                            type="button"
                            class="popup-count working-count"
                            :class="{ active: activeFilter === 'working' }"
                            @click="activeFilter = 'working'"
                        >
                            {{ workingProjectsCount }} Working
                        </button>

                        <button
                            type="button"
                            class="popup-count completed-count"
                            :class="{ active: activeFilter === 'completed' }"
                            @click="activeFilter = 'completed'"
                        >
                            {{ completedProjectsCount }} Complete
                        </button>

                        <button
                            type="button"
                            class="popup-count assigned-count"
                            :class="{ active: activeFilter === 'on_hold_cancelled' }"
                            @click="activeFilter = 'on_hold_cancelled'"
                        >
                            {{ onHoldCancelledProjectsCount }} On Hold / Cancelled
                        </button>
                    </div>
                </div>

                <!-- LOADING -->
                <div v-if="loading && !hasData" class="popup-message">
                    Loading projects...
                </div>

                <!-- ERROR -->
                <div v-else-if="errorMessage" class="popup-message error-message">
                    <span>{{ errorMessage }}</span>

                    <button
                        type="button"
                        class="retry-button"
                        @click="reloadProjects"
                    >
                        Retry
                    </button>
                </div>

                <!-- EMPTY -->
                <div
                    v-else-if="filteredProjects.length === 0"
                    class="popup-message"
                >
                    No projects found in this category.
                </div>

                <!-- FILTERED PROJECT LIST -->
                <div
                    v-else
                    v-for="project in filteredProjects"
                    :key="project.name"
                    class="project-progress-item"
                >
                    <div class="project-progress-info">
                        <span
                            class="project-name"
                            :title="project.project_name || project.name"
                        >
                            {{ project.project_name || project.name }}
                        </span>

                        <span class="project-percentage">
                            {{ formatProgress(project.progress) }}%
                        </span>
                    </div>

                    <div class="progress-track">
                        <div
                            class="progress-fill"
                            :class="{
                                'is-completed': formatProgress(project.progress) >= 100
                            }"
                            :style="{
                                width: formatProgress(project.progress) + '%'
                            }"
                        ></div>
                    </div>
                </div>

            </div>
        </div>

    </div>
</template>


<script setup>
import { computed, ref } from 'vue'
import { Icon, createResource } from 'frappe-ui'

const projectResource = createResource({
    url: '/api/method/one_compliance.one_compliance.api.executive_dashboard.get_project_status_cards',
    auto: true,
})

// Frappe API responses are wrapped inside a "message" property.
// Support both wrapped and unwrapped responses.
const projectData = computed(() => {
    const response = projectResource.data

    return response?.message ?? response ?? null
})

const hasData = computed(() => {
    return projectData.value !== null &&
        projectData.value !== undefined
})

const loading = computed(() => projectResource.loading)

const errorMessage = computed(() => {
    const error = projectResource.error

    if (!error) {
        return ''
    }

    return error.message || 'Unable to load project information.'
})

const totalProjects = computed(() => {
    return projectData.value?.total_projects ?? 0
})

const assignedProjectsCount = computed(() => {
    return projectData.value?.assigned_projects_count ?? 0
})

const projects = computed(() => {
    return projectData.value?.projects ?? []
})

function formatProgress(value) {
    const progress = Number(value) || 0

    return Math.min(100, Math.max(0, progress))
}

function reloadProjects() {
    projectResource.reload()
}

const workingProjectsCount = computed(() =>
    projects.value.filter(project => project.status === 'Open').length
)

const completedProjectsCount = computed(() =>
    projects.value.filter(project => project.status === 'Completed').length
)

const onHoldCancelledProjectsCount = computed(() =>
    projects.value.filter(project =>
        ['On Hold', 'Cancelled'].includes(project.status)
    ).length
)


const assignedOnlyCount = computed(() => {
    return projects.value.filter(
        project => formatProgress(project.progress) === 0
    ).length
})

const activeFilter = ref('all')

const filteredProjects = computed(() => {
    switch (activeFilter.value) {
        case 'working':
            return projects.value.filter(
                project => project.status === 'Open'
            )

        case 'completed':
            return projects.value.filter(
                project => project.status === 'Completed'
            )

        case 'on_hold_cancelled':
            return projects.value.filter(project =>
                ['On Hold', 'Cancelled'].includes(project.status)
            )

        default:
            return projects.value
    }
})

</script>


<style scoped>
.project-status-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
    width: 100%;
    padding: 20px 0;
    box-sizing: border-box;
    position: relative;
    z-index: 20;
}

.status-card {
    position: relative;
    min-width: 0;
    min-height: 126px;
    padding: 16px 18px;
    background: var(--surface-card);
    border: 1px solid var(--border-color);
    border-radius: 4px;

    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0;

    box-shadow:
        0 1px 2px rgba(15, 23, 42, 0.035),
        0 4px 10px rgba(15, 23, 42, 0.045),
        0 10px 24px rgba(15, 23, 42, 0.035);

    transition:
        box-shadow 0.25s ease,
        transform 0.25s ease,
        border-color 0.25s ease;
}

.status-card:hover {
    border-color: #dce4ec;

    box-shadow:
        0 1px 3px rgba(15, 23, 42, 0.045),
        0 4px 10px rgba(15, 23, 42, 0.05),
        0 8px 18px rgba(15, 23, 42, 0.025);

    transform: translateY(-1px);
}
/* STATUS CARD HEADING */

.status-card-header {
    display: flex;
    align-items: center;
    width: 100%;
}

.status-heading {
    display: inline-flex;
    align-items: center;
    gap: 11px;
}

.status-label {
    font-size: 14px;
    font-weight: 500;
    color: #1e293b;
    letter-spacing: -0.015em;
}

/* ICON CONTAINER — MATCHES EMPLOYEE TOOLBAR */

.status-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;

    width: 29px;
    height: 29px;
    padding: 4px;
    box-sizing: border-box;
    flex-shrink: 0;

    color: #334155;
    background: #eff6ff;
    border: 1px solid #dbeafe;
    border-radius: 4px;
}

/* ACTUAL SVG ICON */

.status-icon :deep(svg) {
    width: 18px !important;
    height: 18px !important;
    color: #334155 !important;
    stroke: #334155 !important;
    opacity: 1 !important;
}

.status-icon :deep(svg path),
.status-icon :deep(svg line),
.status-icon :deep(svg circle),
.status-icon :deep(svg rect),
.status-icon :deep(svg polyline) {
    stroke: #334155 !important;
    opacity: 1 !important;
}

.status-value {
    margin-top: 15px;

    font-size: 30px;
    line-height: 1.2;
    font-weight: 700;
    color: var(--text-color);
    font-variant-numeric: tabular-nums;
}


/* PROJECT PROGRESS POPUP */

.project-progress-popup {
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    padding-top: 10px;
    width: 520px;
    min-width: 520px;
    max-width: min(520px, calc(100vw - 30px));
    max-height: 500px;
    overflow-y: auto;
    padding: 22px;

    background: #ffffff;
    opacity: 0;
    visibility: hidden;

    border: 1px solid #e5eaf0;
    border-radius: 4px;

    z-index: 9999;
    isolation: isolate;

    box-shadow:
        0 4px 10px rgba(15, 23, 42, 0.06),
        0 12px 28px rgba(15, 23, 42, 0.10),
        0 22px 45px rgba(15, 23, 42, 0.08);

    box-sizing: border-box;

    transform: translateY(-5px);
    transition:
        opacity 0.18s ease,
        transform 0.18s ease,
        visibility 0.18s ease;
}
.assigned-card::after {
    content: "";
    position: absolute;
    top: 100%;
    left: 0;
    width: 100%;
    height: 8px;
}

.assigned-card:hover .project-progress-popup,
.assigned-card:focus-within .project-progress-popup {
    opacity: 1;
    visibility: visible;
    transform: translateY(0);
}

.assigned-card:hover {
    z-index: 30;
}

.popup-header {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 13px;
    margin-bottom: 22px;
    padding-bottom: 16px;
    border-bottom: 1px solid #edf0f4;
}

.popup-title {
    font-size: 15px;
    font-weight: 450;
    color: #1f2937;
}

.popup-status-group {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
}

.popup-count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 6px 11px;

    border: 1px solid transparent;
    border-radius: 20px;

    font-family: inherit;
    font-size: 11px;
    font-weight: 600;
    white-space: nowrap;

    cursor: pointer;
    transition:
        background 0.18s ease,
        border-color 0.18s ease,
        box-shadow 0.18s ease;
}

.popup-count.active {
    border-color: currentColor;
    box-shadow: 0 0 0 2px rgba(148, 163, 184, 0.10);
}

.popup-count:hover {
    filter: brightness(0.96);
}

.all-count {
    color: #2563eb;
    background: #eff6ff;
}

.assigned-count {
    color: #64748b;
    background: #f1f5f9;
}

.completed-count {
    color: #15803d;
    background: #dcfce7;
}

.working-count {
    color: #b45309;
    background: #fef3c7;
}

.progress-fill.is-completed {
    background-color: #16a34a !important;
}

.project-progress-item {
    margin-bottom: 23px;
}

.project-progress-item:last-child {
    margin-bottom: 0;
}

.project-progress-info {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    margin-bottom: 9px;
}

.project-name {
    font-size: 12px;
    font-weight: 450;
    color: #374151;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.project-percentage {
    flex-shrink: 0;
    font-size: 12px;
    font-weight: 500;
    color: #334155;
    font-variant-numeric: tabular-nums;
}

.progress-track {
    width: 100%;
    height: 7px;
    background: #eef0f3;
    border-radius: 10px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: #3b82f6;
    border-radius: 10px;
    transition: width 0.3s ease;
}

@media (max-width: 600px) {
    .project-status-grid {
        grid-template-columns: minmax(0, 1fr);
        gap: 10px;
        padding: 14px 0;
    }
}
</style>
