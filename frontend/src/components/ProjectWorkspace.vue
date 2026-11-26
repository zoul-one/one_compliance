<template>
    <div class="workspace-grid">
        <!-- SECTION 1: PROJECTS -->
        <section class="workspace-panel" data-tour="my-projects">
            <div class="panel-header project-panel-header">
                <div>
                    <h3>Projects</h3>
                </div>

                <div class="project-header-actions">
                    <div class="project-sort-wrapper">
                        <button
                            type="button"
                            class="project-sort-trigger"
                            title="Sort projects"
                            aria-label="Sort projects"
                            @click.stop="toggleProjectSortMenu($event)"
                        >
                            <Icon name="lucide-filter" />
                        </button>

                    </div>
                    <button
                        v-for="filter in projectFilters"
                        :key="filter.value"
                        class="filter-button"
                        :class="[
                            filterColorClass(filter.value),
                            { active: activeProjectFilter === filter.value }
                        ]"
                        @click="activeProjectFilter = filter.value"
                    >
                        {{ filter.label }}
                    </button>
                </div>
            </div>
            <div class="project-list">
                <div class="project-table-header">
                    <span>NAME</span>
                    <span>CUSTOMER</span>
                    <span>ASSIGNED TO</span>
                </div>
                <div
                    v-for="project in filteredProjects"
                    :key="project.id"
                    class="project-item"
                    :class="{ selected: selectedProject?.id === project.id }"
                    role="button"
                    tabindex="0"
                    @click="selectProject(project)"
                    @keydown.enter="selectProject(project)"
                    @keydown.space.prevent="selectProject(project)"
                >
                    <div class="project-name-cell">
                        <div class="project-item-content">
                            <span class="project-name">{{ project.name }}</span>
                            <span class="project-meta">
                                {{ project.id }} · {{ formatEndDate(project.deadline) }}
                            </span>
                        </div>
                    </div>
                    <div class="project-customer">
                        {{ project.customer }}
                    </div>
                    <div class="project-assignee">
                        <HoverCard
                            v-if="project.assignees.length"
                            side="top"
                            align="start"
                            :hover-delay="200"
                            arrow
                        >
                            <template #trigger>
                                <div
                                    class="assignee-name"
                                    tabindex="0"
                                    :aria-label="`Assigned to: ${project.assignedTo}`"
                                >
                                    {{ project.assignedTo }}
                                </div>
                            </template>

                            <template #default>
                                <div class="assignee-hover-card">
                                    <div class="assignee-hover-card-title">
                                        Assigned to
                                    </div>
                                    <ul>
                                        <li
                                            v-for="(assignee, index) in project.assignees"
                                            :key="`${project.id}-assignee-${index}`"
                                        >
                                            {{ assignee }}
                                        </li>
                                    </ul>
                                </div>
                            </template>
                        </HoverCard>
                        <div v-else class="assignee-name">
                            Unassigned
                        </div>
                    </div>
                </div>
                <div v-if="workspaceResource.loading" class="empty-state">
                    Loading your projects...
                </div>
                <div v-else-if="workspaceResource.error" class="empty-state">
                    Unable to load projects. Please refresh the page and try again.
                </div>
                <div v-else-if="!filteredProjects.length" class="empty-state">
                    No projects are currently assigned to you.
                </div>
            </div>
            <div class="panel-footer">
                <Button
                    variant="outline"
                    theme="gray"
                    size="sm"
                    class="footer-button"
                    :disabled="!projects.length"
                    @click="showAllProjects = true"
                >
                    View All Projects
                    <template #suffix>
                        <Icon name="lucide-arrow-up-right" />
                    </template>
                </Button>
            </div>
        </section>
        <!-- SECTION 2: TASKS -->
        <section class="workspace-panel" data-tour="project-tasks">
            <div class="panel-header task-panel-header">
                <div>
                    <h3>Project Tasks</h3>
                    <p>{{ selectedProject?.name || 'Select a project' }}</p>
                </div>
                <div class="task-header-actions">
                    <button
                        v-for="filter in taskFilters"
                        :key="filter.value"
                        class="filter-button"
                        :class="[
                            filterColorClass(filter.value),
                            { active: activeFilter === filter.value }
                        ]"
                        @click="activeFilter = filter.value"
                    >
                        {{ filter.label }}
                    </button>
                </div>
            </div>
            <div class="task-list">
                <template v-if="selectedProject">
                    <div class="task-table-header">
                        <span>Name</span>
                        <span>Deadline</span>
                        <span>Status</span>
                        <span>Quick Actions</span>
                    </div>
                    <div
                        v-for="task in filteredTasks"
                        :key="task.id"
                        class="task-item"
                    >
                        <div class="task-item-content">
                            <HoverCard side="top" align="start" :hover-delay="200" arrow>
                                <template #trigger>
                                    <span class="task-name">{{ task.description }}</span>
                                </template>

                                <template #default>
                                    <div class="task-name-hover-card">
                                        {{ task.description }}
                                    </div>
                                </template>
                            </HoverCard>
                            <span class="task-id">{{ task.id }}</span>
                        </div>
                        <div class="task-end-date">
                            {{ formatEndDate(task.endDate) }}
                        </div>
                        <div class="task-status">
                            <Badge :theme="statusTheme(task.status)">
                                {{ task.status }}
                            </Badge>
                        </div>
                        <div class="task-quick-actions">
                            <button
                                v-if="!isTaskTimerActive(task)"
                                type="button"
                                class="task-action-button"
                                title="Start Task"
                                :disabled="!canStartTask(task) || startingTask === task.id"
                                @click="startTaskTimer(task)"
                            >
                                <Icon
                                    :name="startingTask === task.id
                                        ? 'lucide-loader-circle'
                                        : 'lucide-play'"
                                />
                            </button>
                            <button
                                v-else
                                type="button"
                                class="task-action-button"
                                title="Create Timesheet Entry"
                                @click="openTimeEntry(task)"
                            >
                                <Icon name="lucide-clock" />
                            </button>
                            <button
                                v-if="!['Completed', 'Cancelled'].includes(task.status)"
                                type="button"
                                class="task-action-button"
                                title="Update Task Status"
                                @click="openTaskStatusDialog(task)"
                            >
                                <Icon name="lucide-check-circle" />
                            </button>
                            <button
                                type="button"
                                class="task-action-button"
                                title="View Customer Documents"
                                @click="openCustomerDocuments(task)"
                            >
                                <Icon name="lucide-file-text" />
                            </button>
                            <button
                                type="button"
                                class="task-action-button"
                                title="View Customer Credentials"
                                @click="openCustomerCredentials(task)"
                            >
                                <Icon name="lucide-key-round" />
                            </button>
                            <button
                                type="button"
                                class="task-action-button"
                                title="Add Payment Details"
                                @click="openPaymentDialog(task)"
                            >
                                <Icon name="lucide-wallet" />
                            </button>
                        </div>
                    </div>
                    <div v-if="!filteredTasks.length" class="empty-state">
                        No tasks found for this filter.
                    </div>
                </template>
                <div v-else-if="workspaceResource.loading" class="empty-state">
                    Loading project tasks...
                </div>
                <div v-else class="empty-state">
                    Select a project to view its tasks.
                </div>
            </div>
            <div class="panel-footer task-footer">
                <Button
                    variant="outline"
                    theme="gray"
                    size="sm"
                    :disabled="!selectedProject"
                    @click="showAllTasks = true"
                >
                    View All Tasks
                     <template #suffix>
                    <Icon name="lucide-arrow-up-right" />
                </template>
                </Button>
            </div>
        </section>

        <div v-if="showProjectSortMenu" class="project-sort-menu" :style="projectSortMenuStyle" @click.stop>
            <button
                type="button"
                :class="{ active: projectSortOrder === 'name' }"
                @click="setProjectSort('name')"
            >
                Project Name (A–Z)
            </button>

            <button
                type="button"
                :class="{ active: projectSortOrder === 'created' }"
                @click="setProjectSort('created')"
            >
                Recently Created
            </button>

            <button
                type="button"
                :class="{ active: projectSortOrder === 'deadline' }"
                @click="setProjectSort('deadline')"
            >
                Deadline (Nearest First)
            </button>
        </div>
        <!-- VIEW ALL PROJECTS POPUP -->
        <div
            v-if="showAllProjects"
            class="modal-backdrop"
            @click.self="showAllProjects = false"
        >
            <section class="workspace-modal">
                <div class="modal-header">
                    <div>
                        <h3>All Assigned Projects</h3>
                        <p>Projects assigned to you</p>
                    </div>
                    <button class="modal-close" @click="showAllProjects = false">
                        <Icon name="lucide-x" />
                    </button>
                </div>
                <div class="modal-project-toolbar">
                    <div class="modal-filter-label">Filters :</div>
                    <div class="project-header-actions">
                        <button
                            type="button"
                            class="project-sort-trigger"
                            title="Sort projects"
                            aria-label="Sort projects"
                            @click.stop="toggleProjectSortMenu($event)"
                        >
                            <Icon name="lucide-filter" />
                        </button>

                        <button
                            v-for="filter in modalProjectFilters"
                            :key="filter.value"
                            class="filter-button"
                            :class="[
                                filterColorClass(filter.value),
                                { active: activeModalProjectFilter === filter.value }
                            ]"
                            @click="activeModalProjectFilter = filter.value"
                        >
                            {{ filter.label }}
                        </button>
                    </div>
                </div>
                <div class="modal-list">
                    <button
                        v-for="project in filteredModalProjects"
                        :key="project.id"
                        class="modal-list-item"
                        @click="selectProjectFromModal(project)"
                    >
                        <div>
                            <strong>{{ project.name }}</strong>
                            <span>
                                {{ project.id }} · {{ formatEndDate(project.deadline) }}
                            </span>
                        </div>
                        <div class="task-modal-actions">
                            <Badge :theme="projectStatusTheme(project.status)">
                                {{ project.status }}
                            </Badge>
                        </div>
                    </button>
                    <div v-if="!filteredModalProjects.length" class="empty-state">
                        No assigned projects available.
                    </div>
                </div>
            </section>
        </div>
        <!-- VIEW ALL TASKS POPUP -->
        <div
            v-if="showAllTasks"
            class="modal-backdrop"
            @click.self="showAllTasks = false"
        >
            <section class="workspace-modal">
                <div class="modal-header">
                    <div>
                        <h3>All Project Tasks</h3>
                        <p>{{ selectedProject?.name }}</p>
                    </div>
                    <button class="modal-close" @click="showAllTasks = false">
                        <Icon name="lucide-x" />
                    </button>
                </div>
                <div class="modal-project-toolbar">
                    <div class="modal-filter-label">Filters :</div>

                    <div class="project-header-actions">
                        <button
                            v-for="filter in modalTaskFilters"
                            :key="filter.value"
                            class="filter-button"
                            :class="[
                                filterColorClass(filter.value),
                                { active: activeModalTaskFilter === filter.value }
                            ]"
                            @click="activeModalTaskFilter = filter.value"
                        >
                            {{ filter.label }}
                        </button>
                    </div>
                </div>

                <div class="modal-list">
                    <div
                        v-for="task in filteredModalTasks"
                        :key="task.id"
                        class="modal-list-item task-modal-item"
                    >
                        <div class="task-modal-details">
                            <strong>{{ task.description }}</strong>
                            <span>{{ task.id }}</span>
                            <span class="task-modal-assignees">
                                Assigned to: {{ task.assignees?.length ? task.assignees.join(', ') : 'Unassigned' }}
                            </span>
                        </div>
                        <div class="task-modal-actions">
                            <Badge :theme="statusTheme(task.status)">
                                {{ task.status }}
                            </Badge>
                            <button
                                type="button"
                                class="task-assignee-add-button"
                                title="Assign more people to this task"
                                @click="openTaskAssigneeDialog(task)"
                            >
                                <Icon name="lucide-user-plus" />
                            </button>
                        </div>
                    </div>
                    <div v-if="!filteredModalTasks.length" class="empty-state">
                        No tasks available for this filter.
                    </div>
                </div>
            </section>
        </div>
    </div>
</template>
<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Badge, Button, Icon, HoverCard, createResource } from 'frappe-ui'
import { matchesProjectFilter } from '../utils/projectFilters'
// --------------------------------------------------
// FETCH PROJECT WORKSPACE DATA
// --------------------------------------------------
const workspaceResource = createResource({
    url: '/api/method/one_compliance.one_compliance.api.executive_dashboard.get_associate_project_workspace',
    auto: true,
})
// Frappe responses may be exposed as either the response's
// message property or directly as the resource data.
const workspaceData = computed(() => {
    const data = workspaceResource.data
    return data?.message ?? data ?? {}
})
// --------------------------------------------------
// ACTIVE TASK TIMER
// --------------------------------------------------
const activeTimers = ref([])
const startingTask = ref(null)
async function loadActiveTimers() {
    try {
        const response = await fetch(
            '/api/method/one_compliance.one_compliance.page.task_management_tool.task_management_tool.get_active_timer'
        )
        const result = await response.json()
        if (!response.ok || result.exc) {
            throw new Error('Unable to retrieve active timers.')
        }
        activeTimers.value = result.message || []
        // Notify the global active timer popup
        window.jQuery(document).trigger(
            'one-compliance-timer-changed',
            [activeTimers.value]
        )
    } catch (error) {
        console.error('Error loading active task timers:', error)
    }
}
onMounted(() => {
    loadActiveTimers()
})
function isTaskTimerActive(task) {
    return activeTimers.value.some(
        timer => timer.task === task.id
    )
}
function canStartTask(task) {
    const restrictedStatuses = ['Completed', 'Hold', 'Cancelled']
    return (
        task.assignees?.length > 0 &&
        !restrictedStatuses.includes(task.status) &&
        !isTaskTimerActive(task)
    )
}
async function startTaskTimer(task) {
    if (!canStartTask(task) || startingTask.value) {
        return
    }
    startingTask.value = task.id
    try {
        // Start the active timer
        const response = await fetch(
            '/api/method/one_compliance.one_compliance.page.task_management_tool.task_management_tool.start_active_timer',
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    task: task.id,
                    project: task.project || '',
                    subject: task.description || '',
                    is_ad_hoc_event: '0',
                    csrf_token: window.frappe.csrf_token,
                }),
            }
        )
        const result = await response.json()
        if (!response.ok || result.exc) {
            throw new Error(
                result.exception || 'Unable to start the task timer.'
            )
        }
        // Update the active timer state
        activeTimers.value = result.message || []

        // Notify the global active timer popup
        window.jQuery(document).trigger(
            'one-compliance-timer-changed',
            [activeTimers.value]
        )

        // Change the Task status to Working
        const statusResponse = await fetch(
            '/api/method/one_compliance.one_compliance.page.task_management_tool.task_management_tool.update_task_status',
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    task: task.id,
                    status: 'Working',
                    csrf_token: window.frappe.csrf_token,
                }),
            }
        )
        const statusResult = await statusResponse.json()
        if (!statusResponse.ok || statusResult.exc) {
            throw new Error(
                statusResult.exception || 'Timer started, but task status could not be updated.'
            )
        }
        // Refresh workspace data
        await workspaceResource.reload()
    } catch (error) {
        console.error('Error starting task:', error)
        window.frappe.msgprint({
            title: 'Unable to Start Task',
            message: error.message,
            indicator: 'red',
        })
        // Retrieve the actual timer state in case the timer
        // started successfully but a later operation failed.
        await loadActiveTimers()
    } finally {
        startingTask.value = null
    }
}
// --------------------------------------------------
// TIMESHEET ENTRY
// --------------------------------------------------
async function openTimeEntry(task) {
    let timer = activeTimers.value.find(item => item.task === task.id)
    // Refresh the timer list before opening the entry form.
    if (!timer) {
        await loadActiveTimers()
        timer = activeTimers.value.find(item => item.task === task.id)
    }
    if (!timer) {
        window.frappe.msgprint({
            title: 'Timer Not Found',
            message: 'There is no active timer for this task. Please start the task first.',
            indicator: 'red',
        })
        return
    }
    try {
        const taskResult = await window.frappe.db.get_value(
            'Task',
            task.id,
            'has_external_dependencies'
        )
        const showLagTimeFields = Boolean(
            taskResult.message?.has_external_dependencies
        )
        const assignees = task.assignees || []
        const dialog = new window.frappe.ui.Dialog({
            title: 'Time Entry',
            fields: [
                {
                    label: 'Employee',
                    fieldname: 'employee',
                    fieldtype: 'Select',
                    options: assignees.join('\n'),
                },
                {
                    label: 'Project',
                    fieldname: 'project',
                    fieldtype: 'Link',
                    options: 'Project',
                    default: task.project,
                },
                {
                    label: 'From Time',
                    fieldname: 'from_time',
                    fieldtype: 'Datetime',
                    reqd: 1,
                    read_only: 1,
                    default: timer.start_time,
                },
                { fieldtype: 'Column Break' },
                {
                    label: 'Task',
                    fieldname: 'task',
                    fieldtype: 'Link',
                    options: 'Task',
                    default: task.id,
                },
                {
                    label: 'Activity',
                    fieldname: 'activity',
                    fieldtype: 'Link',
                    options: 'Activity Type',
                    reqd: 1,
                },
                {
                    label: 'To Time',
                    fieldname: 'to_time',
                    fieldtype: 'Datetime',
                    reqd: 1,
                    read_only: 1,
                    default: window.frappe.datetime.now_datetime(),
                },
                {
                    label: 'Lag Time',
                    fieldname: 'lag_time',
                    fieldtype: 'Duration',
                    hidden: !showLagTimeFields,
                },
                {
                    label: 'Reason for Lag Time',
                    fieldname: 'reason_for_lag_time',
                    fieldtype: 'Small Text',
                    hidden: !showLagTimeFields,
                },
                {
                    label: 'Description',
                    fieldname: 'description',
                    fieldtype: 'Small Text',
                },
            ],
            primary_action_label: 'Submit',
            primary_action(values) {
                if (!values) return
                // Preserve the original workflow: stop the timer,
                // then create the Timesheet entry.
                window.frappe.call({
                    method: 'one_compliance.one_compliance.page.task_management_tool.task_management_tool.stop_active_timer',
                    args: { task: task.id },
                    callback(stopResponse) {
                        activeTimers.value = stopResponse.message || []
                        window.jQuery(document).trigger(
                            'one-compliance-timer-changed',
                            [activeTimers.value]
                        )
                        window.frappe.call({
                            method: 'one_compliance.one_compliance.page.task_management_tool.task_management_tool.create_timesheet',
                            args: values,
                            callback: async function () {
                                window.frappe.msgprint('Timesheet created successfully!')
                                dialog.hide()
                                await loadActiveTimers()
                                await workspaceResource.reload()
                            },
                            error(error) {
                                window.frappe.msgprint({
                                    title: 'Error Creating Timesheet',
                                    message: error.message || 'Unable to create the Timesheet.',
                                    indicator: 'red',
                                })
                            },
                        })
                    },
                    error(error) {
                        window.frappe.msgprint({
                            title: 'Unable to Stop Timer',
                            message: error.message || 'Unable to stop the task timer.',
                            indicator: 'red',
                        })
                    },
                })
            },
        })
        // Match the original page: default to the logged-in user's
        // Employee record; Administrator falls back to the first assignee.
        let employeeName = null
        if (window.frappe.session.user === 'Administrator') {
            employeeName = assignees[0] || null
        } else {
            const employeeResult = await window.frappe.db.get_value(
                'Employee',
                { user_id: window.frappe.session.user },
                'employee_name'
            )
            employeeName = employeeResult.message?.employee_name || null
        }
        if (employeeName) {
            dialog.set_value('employee', employeeName)
        }
        dialog.show()
    } catch (error) {
        console.error('Unable to open Timesheet entry:', error)
        window.frappe.msgprint({
            title: 'Unable to Open Time Entry',
            message: error.message || 'Unable to load the task details.',
            indicator: 'red',
        })
    }
}
// --------------------------------------------------
// COMPLETE / UPDATE TASK STATUS
// --------------------------------------------------
function openTaskStatusDialog(task) {
    window.frappe.call({
        method: 'one_compliance.one_compliance.page.task_management_tool.task_management_tool.get_active_timer_for_task',
        args: { task: task.id },
        callback(response) {
            if (response.message) {
                const activeTimer = response.message
                if (activeTimer.user === window.frappe.session.user) {
                    window.frappe.msgprint({
                        title: 'Not Allowed',
                        message: 'This task is currently running. Please stop the timer before marking it as Completed.',
                        indicator: 'red',
                    })
                } else {
                    const person = activeTimer.full_name || activeTimer.user
                    window.frappe.msgprint({
                        title: 'Not Allowed',
                        message: `${person} is working on it.`,
                        indicator: 'red',
                    })
                }
                return
            }
            window.frappe.model.with_doctype('Task', () => {
                const meta = window.frappe.get_meta('Task')
                const statusField = meta.fields.find(
                    field => field.fieldname === 'status'
                )
                const excludedStatuses = ['Template', 'Cancelled', 'Overdue']
                const statusOptions = (statusField?.options || '')
                    .split('\n')
                    .filter(option => option && !excludedStatuses.includes(option))
                    .join('\n')
                const dialog = new window.frappe.ui.Dialog({
                    title: 'Update Task Status',
                    fields: [
                        {
                            label: 'Status',
                            fieldname: 'status',
                            fieldtype: 'Select',
                            options: statusOptions,
                            default: 'Completed',
                        },
                        {
                            label: 'Completed By',
                            fieldname: 'completed_by',
                            fieldtype: 'Link',
                            options: 'User',
                            default: window.frappe.session.user,
                        },
                        {
                            label: 'Completed On',
                            fieldname: 'completed_on',
                            fieldtype: 'Date',
                            default: window.frappe.datetime.get_today(),
                        },
                    ],
                    primary_action_label: 'Update',
                    primary_action(values) {
                        if (!values) return
                        window.frappe.call({
                            method: 'one_compliance.one_compliance.doc_events.task.update_task_status',
                            args: { task_id: task.id, ...values },
                            callback(result) {
                                if (result.message) {
                                    dialog.hide()
                                    workspaceResource.reload()
                                }
                            },
                        })
                    },
                })
                dialog.show()
            })
        },
    })
}
// --------------------------------------------------
// CUSTOMER DOCUMENTS
// --------------------------------------------------
function openCustomerDocuments(task) {
    if (!task.customer || !task.complianceSubCategory) {
        window.frappe.msgprint({
            title: 'Document Not Available',
            message: 'This task does not have a customer and compliance sub-category linked to it.',
            indicator: 'orange',
        })
        return
    }
    window.frappe.call({
        method: 'one_compliance.one_compliance.utils.view_customer_documents',
        args: {
            customer: task.customer,
            compliance_sub_category: task.complianceSubCategory,
        },
        callback(response) {
            const attachment = response.message?.[0]
            if (!attachment) {
                window.frappe.msgprint({
                    title: 'Document Not Attached',
                    message: 'No document has been attached for this task’s compliance sub-category.',
                    indicator: 'orange',
                })
                return
            }
            const dialog = new window.frappe.ui.Dialog({
                title: 'Document Details',
                fields: [
                    {
                        label: 'Document Attachment',
                        fieldname: 'document_attachment',
                        fieldtype: 'Data',
                        read_only: 1,
                        default: attachment,
                    },
                ],
                primary_action_label: 'Download / Open',
                primary_action() {
                    window.open(attachment, '\_blank', 'noopener')
                },
            })
            dialog.show()
        },
        error(error) {
            window.frappe.msgprint({
                title: 'Document Not Available',
                message: error.message || 'No document is attached for this compliance sub-category.',
                indicator: 'orange',
            })
        },
    })
}
// --------------------------------------------------
// CUSTOMER CREDENTIALS
// --------------------------------------------------
function openCustomerCredentials(task) {
    if (!task.customer || !task.complianceSubCategory) {
        window.frappe.msgprint({
            title: 'Credentials Not Available',
            message: 'This task does not have a customer and compliance sub-category linked to it.',
            indicator: 'orange',
        })
        return
    }
    const purposeDialog = new window.frappe.ui.Dialog({
        title: 'Select Credential Purpose',
        fields: [
            {
                label: 'Purpose',
                fieldname: 'purpose',
                fieldtype: 'Link',
                options: 'Credential Type',
                reqd: 1,
                get_query() {
                    return {
                        filters: {
                            compliance_sub_category: task.complianceSubCategory,
                        },
                    }
                },
            },
        ],
        primary_action_label: 'View Credential',
        primary_action(values) {
            if (!values?.purpose) {
                window.frappe.msgprint('Please select a Purpose before viewing credentials.')
                return
            }
            window.frappe.call({
                method: 'one_compliance.one_compliance.utils.view_credential_details',
                args: {
                    customer: task.customer,
                    purpose: values.purpose,
                },
                callback(response) {
                    const credential = response.message
                    if (!credential || credential.length < 3) {
                        window.frappe.msgprint({
                            title: 'Credential Not Available',
                            message: 'No credential is configured for the selected Purpose.',
                            indicator: 'orange',
                        })
                        return
                    }
                    purposeDialog.hide()
                    const detailsDialog = new window.frappe.ui.Dialog({
                        title: 'Credential Details',
                        fields: [
                            {
                                label: 'Username',
                                fieldname: 'username',
                                fieldtype: 'Data',
                                read_only: 1,
                                default: credential[0],
                            },
                            {
                                label: 'Password',
                                fieldname: 'password',
                                fieldtype: 'Data',
                                read_only: 1,
                                default: credential[1],
                            },
                            {
                                label: 'URL',
                                fieldname: 'url',
                                fieldtype: 'Data',
                                read_only: 1,
                                default: credential[2],
                            },
                        ],
                        primary_action_label: 'Close',
                        primary_action() {
                            detailsDialog.hide()
                        },
                        secondary_action_label: 'Go To URL',
                        secondary_action() {
                            if (credential[2]) {
                                window.open(credential[2], '\_blank', 'noopener')
                            }
                        },
                    })
                    detailsDialog.show()
                },
                error(error) {
                    window.frappe.msgprint({
                        title: 'Unable to Retrieve Credentials',
                        message: error.message || 'Unable to retrieve credentials for this Purpose.',
                        indicator: 'red',
                    })
                },
            })
        },
    })
    purposeDialog.show()
}
// --------------------------------------------------
// WALLET / PAYMENT DETAILS
// --------------------------------------------------
async function openPaymentDialog(task) {
    try {
        // Load the Task's existing payment details so the popup can
        // retain the previous values, as the original page did.
        const taskResponse = await window.frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Task',
                name: task.id,
            },
        })
        const taskDocument = taskResponse.message || {}
        const paymentRows = taskDocument.custom_task_payment_informations || []
        const previousPayment = paymentRows.length
            ? paymentRows[paymentRows.length - 1]
            : {}
        const dialog = new window.frappe.ui.Dialog({
            title: 'Add Payment Info',
            fields: [
                {
                    label: 'Task',
                    fieldname: 'task',
                    fieldtype: 'Link',
                    options: 'Task',
                    default: task.id,
                    read_only: 1,
                },
                {
                    label: 'Payable Amount',
                    fieldname: 'payable_amount',
                    fieldtype: 'Currency',
                    reqd: 1,
                    default: previousPayment.payable_amount || 0,
                    non_negative: 1,
                },
                {
                    label: 'Mode of Payment',
                    fieldname: 'mode_of_payment',
                    fieldtype: 'Link',
                    options: 'Mode of Payment',
                    reqd: 1,
                    only_select: 1,
                    default: previousPayment.mode_of_payment || '',
                    change() {
                        const modeOfPayment = dialog.get_value('mode_of_payment')
                        if (modeOfPayment) {
                            window.frappe.db.get_value(
                                'Mode of Payment',
                                modeOfPayment,
                                'type'
                            ).then(({ message }) => {
                                dialog.set_value('type', message?.type || '')
                            })
                        } else {
                            dialog.set_value('type', '')
                        }
                    },
                },
                {
                    label: 'Type',
                    fieldname: 'type',
                    fieldtype: 'Data',
                    read_only: 1,
                    hidden: 1,
                    default: previousPayment.type || '',
                },
                { fieldtype: 'Column Break' },
                {
                    label: 'Reference Number',
                    fieldname: 'reference_number',
                    fieldtype: 'Data',
                    default: previousPayment.reference_number || '',
                    mandatory_depends_on: "eval:doc.type == 'Bank'",
                },
                {
                    label: 'Reference Date',
                    fieldname: 'reference_date',
                    fieldtype: 'Date',
                    default: previousPayment.reference_date || '',
                    mandatory_depends_on: "eval:doc.type == 'Bank'",
                },
                {
                    label: 'User Remark',
                    fieldname: 'user_remark',
                    fieldtype: 'Small Text',
                    reqd: 1,
                    default: previousPayment.user_remark || '',
                },
            ],
            primary_action_label: 'Save',
            primary_action(values) {
                if (!values) return
                window.frappe.call({
                    method: 'one_compliance.one_compliance.page.task_management_tool.task_management_tool.add_payment_info',
                    args: {
                        task_id: task.id,
                        payable_amount: values.payable_amount,
                        mode_of_payment: values.mode_of_payment,
                        reference_number: values.reference_number,
                        reference_date: values.reference_date,
                        user_remark: values.user_remark,
                        type: values.type,
                    },
                    callback() {
                        window.frappe.msgprint('Payment info added successfully!')
                        dialog.hide()
                        workspaceResource.reload()
                    },
                    error(error) {
                        window.frappe.msgprint({
                            title: 'Error Adding Payment Info',
                            message: error.message || 'Unable to save payment information.',
                            indicator: 'red',
                        })
                    },
                })
            },
        })
        dialog.show()
    } catch (error) {
        console.error('Unable to load task payment details:', error)
        window.frappe.msgprint({
            title: 'Unable to Open Payment Dialog',
            message: error.message || 'Unable to load the task payment details.',
            indicator: 'red',
        })
    }
}
// --------------------------------------------------
// TASK-LEVEL ASSIGNMENTS
// --------------------------------------------------
function openTaskAssigneeDialog(task) {
    if (!task?.id) return
    const dialog = new window.frappe.ui.Dialog({
        title: 'Add Employees',
        fields: [
            {
                label: 'Assign To',
                fieldname: 'assign_to',
                fieldtype: 'MultiSelectPills',
                get_data(txt) {
                    return window.frappe.db.get_link_options('User', txt, {
                        user_type: 'System User',
                        enabled: 1,
                    })
                },
            },
        ],
        primary_action_label: 'Add',
        primary_action(values) {
            const selectedUsers = values?.assign_to
            if (!selectedUsers || !selectedUsers.length) {
                window.frappe.msgprint('Please select at least one user.')
                return
            }
            window.frappe.call({
                method: 'frappe.desk.form.assign_to.add',
                args: {
                    doctype: 'Task',
                    name: task.id,
                    assign_to: selectedUsers,
                },
                callback() {
                    dialog.hide()
                    window.frappe.msgprint('Task assigned successfully!')
                    workspaceResource.reload()
                },
                error(error) {
                    window.frappe.msgprint({
                        title: 'Unable to Assign Task',
                        message: error.message || 'The task assignments could not be saved.',
                        indicator: 'red',
                    })
                },
            })
        },
    })
    // Keep the Frappe dialog above the Vue task-list popup.
    dialog.$wrapper.css('z-index', 10001)
    // The task-list popup already dims the page. Make only the extra
    // Bootstrap backdrop created by this dialog transparent to avoid
    // stacking a second dark overlay, while keeping its modal behavior.
    dialog.show()

    // Immediately make the newly created backdrop transparent.
    window.jQuery('.modal-backdrop').last().css({
        opacity: 0,
        background: 'transparent',
    })
}
// --------------------------------------------------
// Convert the backend response into the property names
// already used by this component's template.
const projects = computed(() =>
    (workspaceData.value.projects || []).map(project => ({
        id: project.name,
        name: project.project_name || project.name,
        customer: project.customer_name || project.customer || '—',
        assignees: project.assignees || [],
        assignedTo: (project.assignees || []).join(', ') || 'Unassigned',
        deadline: project.expected_end_date || null,
        createdOn: project.creation || null,
        status: project.status || '—',
        progress: Number(project.progress || 0),
        totalTasks: Number(project.total_tasks || 0),
        completedTasks: Number(project.completed_tasks || 0),
        tasks: (project.tasks || []).map(task => ({
            id: task.name,
            description: task.subject || task.name,
            status: task.status || '—',
            priority: task.priority || '—',
            startDate: task.start_date || null,
            endDate: task.deadline || null,
            deadlineState: task.deadline_state || null,
            progress: Number(task.progress || 0),
            assignees: task.assignees || [],
            // Additional fields for task actions
            project: task.project,
            projectName: task.project_name,
            customer: task.customer,
            customerName: task.customer_name,
            complianceSubCategory: task.compliance_sub_category,
        })),
    }))
)
// The backend already returns projects assigned to the logged-in user.
// Do not filter by a made-up "Active" status: Completed and On Hold
// projects can also be assigned projects.


// --------------------------------------------------
// PROJECT SORTING
// --------------------------------------------------

const showProjectSortMenu = ref(false)
const projectSortOrder = ref('created')
const projectSortMenuStyle = ref({})


function toggleProjectSortMenu(event) {
    if (showProjectSortMenu.value) {
        showProjectSortMenu.value = false
        return
    }
    // Place menu under the filter button, using screen position
    const rect = event.currentTarget.getBoundingClientRect()
    projectSortMenuStyle.value = {
        top: `${rect.bottom + 6}px`,
        left: `${rect.left}px`,
    }
    showProjectSortMenu.value = true
}

function closeProjectSortMenu() {
    showProjectSortMenu.value = false
}

function setProjectSort(order) {
    projectSortOrder.value = order
    closeProjectSortMenu()
}

// Close on outside click, scroll or resize (fixed menu would float away)
onMounted(() => {
    document.addEventListener('click', closeProjectSortMenu)
    window.addEventListener('scroll', closeProjectSortMenu, true)
    window.addEventListener('resize', closeProjectSortMenu)
})

onBeforeUnmount(() => {
    document.removeEventListener('click', closeProjectSortMenu)
    window.removeEventListener('scroll', closeProjectSortMenu, true)
    window.removeEventListener('resize', closeProjectSortMenu)
})

const sortedProjects = computed(() => {
    const list = [...projects.value]

    // Sort alphabetically by project name
    if (projectSortOrder.value === 'name') {
        return list.sort((a, b) =>
            a.name.localeCompare(b.name, undefined, {
                numeric: true,
                sensitivity: 'base',
            })
        )
    }

    // Sort by nearest deadline first
    if (projectSortOrder.value === 'deadline') {
        return list.sort((a, b) => {
            // Projects without deadlines go to the bottom
            if (!a.deadline) return 1
            if (!b.deadline) return -1

            return new Date(a.deadline) - new Date(b.deadline)
        })
    }

    // Use creation dates if every project has one
    const hasCreationDates = list.every(project => project.createdOn)

    if (hasCreationDates) {
        return list.sort(
            (a, b) => new Date(b.createdOn) - new Date(a.createdOn)
        )
    }

    // Otherwise, use project number (higher number = newer)
    return list.sort((a, b) =>
        b.id.localeCompare(a.id, undefined, {
            numeric: true,
            sensitivity: 'base',
        })
    )
})
// --------------------------------------------------
// PROJECT FILTERS
// --------------------------------------------------

const projectFilters = [
    { label: 'All', value: 'All' },
    { label: 'Working', value: 'Working' },
    { label: 'Complete', value: 'Completed' },
]

const modalProjectFilters = [
    ...projectFilters,
    { label: 'Overdue', value: 'Overdue' },
]
function filterColorClass(value) {
    const colors = {
        All: 'filter-blue',
        Open: 'filter-yellow',
        Working: 'filter-yellow',
        Completed: 'filter-green',
        Complete: 'filter-green',
        'On Hold / Cancelled': 'filter-gray',
        Overdue: 'filter-red',
    }

    return colors[value] || 'filter-gray'
}

const activeProjectFilter = ref('All')
const activeModalProjectFilter = ref('All')


const filteredProjects = computed(() =>
    sortedProjects.value.filter(project =>
        matchesProjectFilter(project, activeProjectFilter.value)
    )
)

const filteredModalProjects = computed(() =>
    sortedProjects.value.filter(project =>
        matchesProjectFilter(project, activeModalProjectFilter.value)
    )
)

// --------------------------------------------------
// PROJECT SELECTION AND TASK FILTERS
// --------------------------------------------------
const selectedProject = ref(null)
// The API loads asynchronously. Select the first project after
// the response arrives, and keep the selected object fresh on reload.
watch(
    projects,
    (projectList) => {
        if (!projectList.length) {
            selectedProject.value = null
            return
        }

        const currentProject = projectList.find(
            project => project.id === selectedProject.value?.id
        )

        selectedProject.value = currentProject || projectList[0]
    },
    { immediate: true }
)
const projectTasks = computed(() =>
    selectedProject.value?.tasks || []
)
const taskFilters = [
    { label: 'All', value: 'All' },
    { label: 'Working', value: 'Working' },
    { label: 'Completed', value: 'Completed' },
]

// The All Project Tasks popup has an additional dedicated Overdue filter.
const modalTaskFilters = [
    ...taskFilters,
    { label: 'Overdue', value: 'Overdue' },
]

const activeFilter = ref('All')
const activeModalTaskFilter = ref('All')

// Overdue is a separate Task status in this app, and the backend can also
// flag an otherwise Working task as overdue through its deadline_state.
// Both cases belong in the Working filter so overdue work is not hidden.
function matchesTaskFilter(task, filter) {
    if (filter === 'All') return true
    if (filter === 'Overdue') {
        return task.status === 'Overdue'
            || (
                task.deadlineState === 'Overdue'
                && !['Completed', 'Cancelled'].includes(task.status)
            )
    }
    if (filter === 'Working') {
        return task.status === 'Working'
            || task.status === 'Overdue'
            || (
                task.deadlineState === 'Overdue'
                && !['Completed', 'Cancelled'].includes(task.status)
            )
    }
    return task.status === filter
}

const filteredModalTasks = computed(() =>
    projectTasks.value.filter(task =>
        matchesTaskFilter(task, activeModalTaskFilter.value)
    )
)

const filteredTasks = computed(() =>
    projectTasks.value.filter(task =>
        matchesTaskFilter(task, activeFilter.value)
    )
)

function selectProject(project) {
    selectedProject.value = project
    activeFilter.value = 'All'
    activeModalTaskFilter.value = 'All'
}
function selectProjectFromModal(project) {
    selectProject(project)
    showAllProjects.value = false
}
// --------------------------------------------------
// DATE FORMATTING
// --------------------------------------------------
function formatEndDate(date) {
    if (!date) return 'No deadline'
    const [year, month, day] = date.split('-')
    if (!year || !month || !day) return date
    return `${day}/${month}/${year}`
}
// --------------------------------------------------
// POPUP STATE
// --------------------------------------------------
const showAllProjects = ref(false)
const showAllTasks = ref(false)
// --------------------------------------------------
// STATUS BADGE THEMES
// --------------------------------------------------
function statusTheme(status) {
    const themes = {
        Working: 'blue',
        Completed: 'green',
        Pending: 'orange',
        'Pending Review': 'orange',
        Overdue: 'red',
        Cancelled: 'gray',
        Open: 'orange',
    }
    return themes[status] || 'gray'
}
function projectStatusTheme(status) {
    const themes = {
        Completed: 'green',
        Open: 'blue',
        Overdue: 'red',
        'On Hold': 'orange',
        Cancelled: 'gray',
    }
    return themes[status] || 'gray'
}
</script>
<style scoped>
.workspace-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
    width: 100%;
    align-items: stretch;
}
.workspace-panel {
    min-width: 0;
    height: 430px;
    display: flex;
    flex-direction: column;
    background: var(--surface-card);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    box-shadow:
        0 1px 2px rgba(15, 23, 42, 0.035),
        0 4px 10px rgba(15, 23, 42, 0.045),
        0 10px 24px rgba(15, 23, 42, 0.035);
    overflow: hidden;
}
.panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 16px 12px;
    border-bottom: 1px solid var(--border-color);
}
.panel-header h3 {
    margin: 0;
    font-size: 14px;
    font-weight: 450;
    color: var(--text-color);
}
.panel-header p {
    margin: 4px 0 0;
    font-size: 11px;
    color: var(--text-muted);
}
.panel-icon {
    width: 19px;
    height: 19px;
    color: var(--text-muted);
}
.project-list,
.task-list {
    position: relative;
    flex: 1;
    min-height: 0;
    overflow-y: auto;

    /* Thin scrollbar */
    scrollbar-width: thin;
    scrollbar-color: #cbd5e1 transparent;
}

/* Chrome, Edge and other WebKit-based browsers */
.project-list::-webkit-scrollbar,
.task-list::-webkit-scrollbar {
    width: 5px;
}

.project-list::-webkit-scrollbar-track,
.task-list::-webkit-scrollbar-track {
    background: transparent;
}

.project-list::-webkit-scrollbar-thumb,
.task-list::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 10px;
}

.project-list::-webkit-scrollbar-thumb:hover,
.task-list::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
}
/* PROJECT TABLE HEADER */
.project-table-header {
    display: grid;
    grid-template-columns: minmax(0, 1.4fr) minmax(90px, 0.9fr) minmax(110px, 1fr);
    gap: 10px;
    align-items: center;
    padding: 11px 14px;
    background: var(--surface-gray-2);
    border-bottom: 1px solid var(--border-color);
    position: sticky;
    top: 0;
    z-index: 2;
}
.project-table-header span:last-child {
    padding-left: 8px;
}
.project-panel-header {
    gap: 10px;
    min-height: 70px;
    box-sizing: border-box;
}

.project-panel-header > div:first-child,
.task-panel-header > div:first-child {
    transform: translateY(-3px);
}

.project-header-actions {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 5px;
    flex-shrink: 0;
}

.project-sort-wrapper {
    flex-shrink: 0;
}

.project-sort-trigger {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    padding: 0;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
}

.project-sort-trigger:hover {
    color: var(--blue-600);
    background: var(--surface-blue-1);
}

.project-sort-trigger :deep(svg) {
    width: 15px;
    height: 15px;
}

.project-sort-menu {
    position: fixed;
    z-index: 10001;
    min-width: 200px;
    padding: 5px;
    background: #ffffff;
    border: 1px solid var(--border-color, #e5e7eb);
    border-radius: 7px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
}

.project-sort-menu button {
    display: block;
    width: 100%;
    padding: 8px 10px;
    border: 0;
    border-radius: 4px;
    background: transparent;
    color: var(--text-color);
    text-align: left;
    font-size: 11px;
    cursor: pointer;
}

.project-sort-menu button:hover,
.project-sort-menu button.active {
    background: var(--surface-blue-1);
    color: var(--blue-600);
}
.project-table-header span {
    font-size: 11px;
    font-weight: 600;
    color: var(--text-muted);
}
/* PROJECT ROW */
.project-item {
    width: 100%;
    display: grid;
    grid-template-columns: minmax(0, 1.4fr) minmax(90px, 0.9fr) minmax(110px, 1fr);
    gap: 10px;
    align-items: center;
    padding: 11px 14px;
    text-align: left;
    background: transparent;
    border: 0;
    border-bottom: 1px solid var(--border-color);
    cursor: pointer;
    transition: background 0.15s ease;
    box-sizing: border-box;
}
.project-item:hover {
    background: var(--surface-gray-2);
}
.project-item.selected {
    background: var(--surface-blue-1);
    border-left: 3px solid var(--blue-500);
    padding-left: 11px;
}
/* NAME AND PROJECT CODE */
.project-name-cell {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 5px;
    min-width: 0;
}
.project-customer {
    min-width: 0;
    font-size: 10px;
    color: var(--text-color);
    overflow-wrap: anywhere;
}
.modal-project-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 10px 16px;
    border-bottom: 1px solid #e2e8f0;
    background: #f8fafc;
    overflow: hidden;
    flex-shrink: 0;
}
.modal-filter-label {
    font-size: 16px;
    font-weight: 450;
    color: #000000;
    white-space: nowrap;
}

.modal-project-toolbar .project-header-actions {
    flex-shrink: 0;
}
/* ASSIGNED EMPLOYEE */
.project-assignee {
    min-width: 0;
}
.assignee-name {
    display: block;
    width: 100%;
    min-width: 0;
    padding: 6px 7px;
    border: 1px solid var(--border-color);
    border-radius: 5px;
    background: var(--surface-card);
    color: var(--text-color);
    font-size: 10px;
    text-align: left;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    cursor: default;
}

.assignee-name:focus-visible {
    outline: 2px solid var(--blue-500);
    outline-offset: 2px;
}

.assignee-hover-card {
    min-width: 180px;
    max-width: 300px;
    max-height: 240px;
    overflow-y: auto;
    padding: 10px 12px;
    color: #334155;
    font-size: 12px;
}

.assignee-hover-card-title {
    margin-bottom: 7px;
    color: #64748b;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.assignee-hover-card ul {
    display: flex;
    flex-direction: column;
    gap: 5px;
    margin: 0;
    padding-left: 17px;
}

.assignee-hover-card li {
    overflow-wrap: anywhere;
    line-height: 1.4;
}
/* PROJECT NAME AND META */
.project-item-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
}
.project-name {
    font-size: 12px;
    font-weight: 450;
    color: var(--text-color);
    overflow-wrap: anywhere;
}
.project-item .project-item-content .project-meta {
    font-size: 12px !important;
    color: #94a3b8 !important;
    font-weight: 400;
}
.item-arrow {
    width: 15px;
    height: 15px;
    color: var(--text-muted);
    flex-shrink: 0;
}
.project-item-content,
.task-item-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
}
.project-name,
.task-name {
    font-size: 12px;
    font-weight: 475;
    color: var(--text-color);
    overflow-wrap: anywhere;
}
.project-meta,
.task-id {
    font-size: 10px;
    color: var(--text-muted);
}
.item-arrow {
    width: 15px;
    height: 15px;
    color: var(--text-muted);
    flex-shrink: 0;
}
/* TASK FILTERS IN HEADER */
.task-panel-header {
    gap: 10px;
    min-height: 70px;
    box-sizing: border-box;
}

.task-header-actions {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 5px;
    flex-shrink: 0;
}
.filter-button {
    padding: 5px 11px;
    border: 1px solid transparent;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition:
        background 0.18s ease,
        border-color 0.18s ease,
        box-shadow 0.18s ease;
}

/* BLUE - ALL */
.filter-blue {
    color: #2563eb;
    background: #eff6ff;
    border-color: #bfdbfe;
}

/* YELLOW - WORKING / OPEN */
.filter-yellow {
    color: #b45309;
    background: #fef3c7;
    border-color: #fde68a;
}

/* GREEN - COMPLETED */
.filter-green {
    color: #15803d;
    background: #dcfce7;
    border-color: #bbf7d0;
}

/* RED - OVERDUE */
.filter-red {
    color: #b91c1c;
    background: #fee2e2;
    border-color: #fecaca;
}

/* GREY - ON HOLD / CANCELLED */
.filter-gray {
    color: #64748b;
    background: #f1f5f9;
    border-color: #e2e8f0;
}



.filter-button:hover {
    filter: brightness(0.96);
}

.filter-button.active {
    border-color: currentColor;
    box-shadow: 0 0 0 2px rgba(148, 163, 184, 0.10);
}

.task-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 12px 14px;
    border-bottom: 1px solid var(--border-color);
}
.task-item-content {
    flex: 1;
}
.panel-footer {
    display: flex;
    padding: 12px;
    border-top: 1px solid var(--border-color);
}
.footer-button {
    width: 100%;
    justify-content: center;
}
.task-footer {
    gap: 8px;
}
.task-footer > * {
    flex: 1;
    justify-content: center;
    min-width: 0;
}
.empty-state {
    padding: 30px 12px;
    text-align: center;
    font-size: 12px;
    color: var(--text-muted);
}
/* TASK TABLE HEADER */
/* TASK TABLE HEADER */
.task-table-header {
    display: grid;
    grid-template-columns: minmax(0, 1.8fr) minmax(100px, 0.8fr) minmax(100px, 0.8fr) minmax(150px, 1fr);
    align-items: center;
    gap: 12px;
    padding: 11px 14px;
    background: var(--surface-gray-2);
    border-bottom: 1px solid var(--border-color);
    color: var(--text-muted);
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    /* Keep the heading visible while tasks scroll */
    position: sticky;
    top: 0;
    z-index: 2;
}
/* TASK ROW */
.task-item {
    display: grid;
    grid-template-columns: minmax(0, 1.8fr) minmax(100px, 0.8fr) minmax(100px, 0.8fr) minmax(150px, 1fr);
    align-items: center;
    gap: 12px;
    padding: 13px 14px;
    border-bottom: 1px solid #edf0f2;
    transition: background 0.15s ease;
}
.task-item:hover {
    background: #f8fafc;
}
/* TASK NAME AND ID */
.task-item-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
}
.task-name {
    color: #334155;
    font-size: 13px;
    font-weight: 475;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.task-id {
    color: #94a3b8;
    font-size: 11px;
}
/* END DATE */
.task-end-date {
    color: #64748b;
    font-size: 12px;
    white-space: nowrap;
}
/* STATUS */
.task-status {
    display: flex;
    align-items: center;
}
/* QUICK ACTION ICONS */
.task-quick-actions {
    display: flex;
    align-items: center;
    gap: 7px;
}
.task-action-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 30px;
    flex-shrink: 0;
    border: none;
    border-radius: 0;
    background: transparent;
    color: #64748b;
    cursor: pointer;
    transition: color 0.15s ease;
}
.task-action-button:disabled {
    cursor: not-allowed;
    opacity: 0.4;
}
.task-action-button:disabled:hover {
    color: #64748b;
}
.task-action-button:hover {
    background: transparent;
    color: #1e293b;
}
.task-action-button :deep(svg) {
    width: 16px;
    height: 16px;
}
/* SMALLER SCREENS */
@media (max-width: 650px) {
    .task-table-header,
    .task-item {
        grid-template-columns: minmax(130px, 1.5fr) minmax(85px, 0.8fr) minmax(85px, 0.8fr) minmax(130px, 1fr);
        gap: 8px;
        padding-left: 10px;
        padding-right: 10px;
    }
    .task-quick-actions {
        gap: 4px;
    }
    .task-action-button {
        width: 27px;
        height: 27px;
    }
}
/* POPUP BACKDROP */
.modal-backdrop {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    box-sizing: border-box;
    padding: 20px;

    background: rgba(15, 23, 42, 0.58);

    /* Blur the dashboard behind the popup */
    backdrop-filter: blur(5px);
    -webkit-backdrop-filter: blur(5px);

    overflow-y: auto;
}
/* POPUP CONTAINER */
.workspace-modal {
    display: flex;
    flex-direction: column;
    width: 100%;
    max-width: 600px;
    max-height: calc(100vh - 40px);
    min-height: 0;
    background: #ffffff;
    color: #1f2937;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    box-shadow: 0 18px 50px rgba(0, 0, 0, 0.25);
    overflow: hidden;
    opacity: 1;
    box-sizing: border-box;
}
.modal-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    padding: 18px 20px;
    background: #ffffff;
    border-bottom: 1px solid #e5e7eb;
    flex-shrink: 0;
}
.modal-header h3 {
    margin: 0;
    font-size: 16px;
    color: #111827;
}
.modal-header p {
    margin: 5px 0 0;
    font-size: 11px;
    color: #6b7280;
}
.modal-close {
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 0;
    border-radius: 6px;
    background-color: #f3f4f6;
    color: #374151;
    cursor: pointer;
    flex-shrink: 0;
}
.modal-close:hover {
    background-color: #e5e7eb;
}
.modal-close :deep(svg) {
    width: 16px;
    height: 16px;
}
.modal-list {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    background: #ffffff;
    overscroll-behavior: contain;
}
.modal-list-item {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 13px 20px;
    text-align: left;
    background-color: #ffffff;
    color: #1f2937;
    border: 0;
    border-bottom: 1px solid #e5e7eb;
}
button.modal-list-item {
    cursor: pointer;
}
button.modal-list-item:hover {
    background-color: #f9fafb;
}
.modal-list-item > div {
    display: flex;
    flex-direction: column;
    gap: 5px;
    min-width: 0;
}
.modal-list-item strong {
    font-weight: 475;
    font-size: 12px;
    color: #1f2937;
}
.modal-list-item > div > span {
    font-size: 10px;
    color: #6b7280;
}
.task-modal-item {
    align-items: center;
}
.task-modal-details {
    flex: 1;
}
.task-modal-assignees {
    margin-top: 2px;
    overflow-wrap: anywhere;
}
.modal-list-item > .task-modal-actions {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
}
.task-assignee-add-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    padding: 0;
    border: 1px solid #d1d5db;
    border-radius: 5px;
    background: #ffffff;
    color: #6b7280;
    cursor: pointer;
}
.task-assignee-add-button:hover {
    background: #f3f4f6;
    color: #1f2937;
}
.task-assignee-add-button :deep(svg) {
    width: 15px;
    height: 15px;
}
.update-modal {
    max-width: 480px;
    max-height: calc(100vh - 40px);
    overflow-y: auto;
}
.update-form {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 20px;
    background-color: #ffffff;
}
.update-form label {
    margin-top: 5px;
    font-size: 11px;
    font-weight: 600;
    color: #374151;
}
.update-form select,
.update-form textarea {
    width: 100%;
    box-sizing: border-box;
    padding: 9px 10px;
    font: inherit;
    font-size: 12px;
    color: #1f2937;
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
}
.update-form textarea {
    resize: vertical;
}
.modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding: 14px 20px;
    background-color: #ffffff;
    border-top: 1px solid #e5e7eb;
    flex-shrink: 0;
}

.task-name-hover-card {
    max-width: 320px;
    padding: 10px 12px;
    font-size: 12px;
    line-height: 1.5;
    color: #334155;
    white-space: normal;
    overflow-wrap: anywhere;
}
/* RESPONSIVE */
@media (max-width: 1100px) {
    .workspace-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .workspace-panel:last-child {
        grid-column: 1 / -1;
    }
}
@media (max-width: 650px) {
    .workspace-grid {
        grid-template-columns: minmax(0, 1fr);
    }
    .workspace-panel:last-child {
        grid-column: auto;
    }
    .modal-backdrop {
        padding: 12px;
    }
    .workspace-modal {
        max-height: calc(100vh - 24px);
    }
}
@media (max-width: 500px) {
    .workspace-panel {
        height: 400px;
    }
    .task-footer {
        flex-direction: column;
    }
    .project-table-header,
    .project-item {
        grid-template-columns: minmax(0, 1.2fr) minmax(75px, 0.8fr) minmax(95px, 1fr);
        gap: 6px;
        padding-left: 9px;
        padding-right: 9px;
    }
    .project-item.selected {
        padding-left: 6px;
    }
}

</style>
