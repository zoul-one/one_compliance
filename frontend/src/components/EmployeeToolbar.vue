<template>
    <div class="associate-dashboard">
        <div class="associate-toolbar">
            <!-- 1. EMPLOYEE DETAILS -->
            <section class="toolbar-section employee-section" data-tour="employee-profile">
                <div class="section-heading">
                    <span class="section-icon">
                        <Icon name="lucide-user-round" />
                    </span>
                    <span>Employee Profile</span>
                </div>
                <div class="employee-profile">
                    <div class="employee-avatar">
                        <Avatar
                            :image="employee.image"
                            :label="employee.name"
                            size="2xl"
                        />
                    </div>
                    <div class="employee-details">
                        <h3>{{ employee.name }}</h3>
                        <span class="employee-id">{{ employee.id }}</span>
                        <Badge theme="blue" class="employee-designation-badge">
                            {{ employee.designation || 'Designation not set' }}
                        </Badge>
                    </div>
                </div>
                <div class="profile-footer">
                    <span class="profile-status">
                        <span class="status-dot"></span>
                        Active
                    </span>
                </div>
            </section>
            <!-- 2. ATTENDANCE -->
            <section class="toolbar-section attendance-section" data-tour="attendance">
                <div class="section-heading">
                    <span class="section-icon">
                        <Icon name="lucide-clock" />
                    </span>

                    <span>Attendance</span>

                    <Badge
                        class="attendance-status-badge"
                        :theme="isCheckedIn ? 'green' : 'gray'"
                    >
                        {{ isCheckedIn ? 'Currently Working' : 'Not Checked In' }}
                    </Badge>
                </div>
                <div class="attendance-action">
                    <Button
                        v-if="!isCheckedIn"
                        variant="solid"
                        theme="green"
                        size="sm"
                        class="attendance-button"
                        :loading="isAttendanceSubmitting"
                        :disabled="isAttendanceSubmitting || !isDaySummaryLoaded"
                        @click="recordAttendance('IN')"
                    >
                        <template #prefix>
                            <Icon
                                name="lucide-circle-arrow-right"
                                class="attendance-arrow-icon"
                            />
                        </template>
                        Check In
                    </Button>

                    <Button
                        v-else
                        variant="solid"
                        theme="green"
                        size="sm"
                        class="attendance-button"
                        :loading="isAttendanceSubmitting"
                        :disabled="isAttendanceSubmitting || !isDaySummaryLoaded"
                        @click="recordAttendance('OUT')"
                    >
                        <template #prefix>
                            <Icon
                                name="lucide-circle-arrow-left"
                                class="attendance-arrow-icon"
                            />
                        </template>
                        Check Out
                    </Button>

                    <p
                        v-if="attendanceMessage"
                        class="attendance-feedback"
                        :class="attendanceMessageType"
                        role="status"
                        aria-live="polite"
                    >
                        {{ attendanceMessage }}
                    </p>
                </div>
                <div class="attendance-times">
                    <div class="time-item">
                        <span class="time-label">
                            <Icon name="lucide-log-in" />
                            Check In
                        </span>
                        <span class="time-value">
                            {{ checkInTime || '--:--' }}
                        </span>
                    </div>

                    <div class="time-item">
                        <span class="time-label">
                            Check Out
                            <Icon name="lucide-log-out" />
                        </span>
                        <span class="time-value">
                            {{ checkOutTime || '--:--' }}
                        </span>
                    </div>
                </div>
            </section>
            <!-- 3. WEEKLY WORKING HOURS -->
            <section class="toolbar-section weekly-section" data-tour="weekly-hours">
                <div class="section-heading">
                    <span class="section-icon">
                        <Icon name="lucide-bar-chart-3" />
                    </span>
                    <span>Weekly Hours</span>
                </div>
                <div class="weekly-summary">
                    <div class="weekly-total">
                        <span class="weekly-hours">{{ totalHours }}</span>
                        <span class="weekly-target">/ {{ weeklyTarget }} hrs</span>
                    </div>
                    <Button
                        variant="subtle"
                        theme="gray"
                        size="sm"
                        class="chart-trigger"
                        title="View weekly working hours"
                        @click="openWeeklyChart"
                    >
                        <Icon name="lucide-chart-no-axes-column" />
                    </Button>
                    <span class="weekly-percentage">
                        {{ weeklyPercentage }}% completed
                    </span>
                </div>
                <div class="weekly-progress-track">
                    <div
                        class="weekly-progress-fill"
                        :style="{ width: `${weeklyPercentage}%` }"
                    ></div>
                </div>
            </section>
            <!-- 4. QUICK ACCESS -->
            <section class="toolbar-section quick-access-section" data-tour="quick-access">
                <div class="section-heading">
                    <span class="section-icon">
                        <Icon name="lucide-grid" />
                    </span>
                    <span>Quick Access</span>
                </div>
                <div class="quick-access-list">
                    <!-- HR MENU -->
                    <div class="hr-menu-wrapper">
                        <Button
                            variant="ghost"
                            theme="gray"
                            size="sm"
                            class="quick-access-button hr-menu-trigger"
                            @click.stop="
                                showHRMenu = !showHRMenu;
                                showTeamMenu = false
                            "
                        >
                            <template #prefix>
                                <Icon name="lucide-users" />
                            </template>
                            HR
                            <template #suffix>
                                <Icon
                                    :name="showHRMenu ? 'lucide-chevron-up' : 'lucide-chevron-down'"
                                />
                            </template>
                        </Button>
                        <div
                            v-if="showHRMenu"
                            class="hr-dropdown"
                            @click.stop
                        >
                            <button
                                class="hr-dropdown-item"
                                @click="navigateToHR('/app/attendance')"
                            >
                                <Icon name="lucide-clock" />
                                <span>Attendance</span>
                            </button>
                            <button
                                class="hr-dropdown-item"
                                @click="navigateToHR('/app/attendance-request')"
                            >
                                <Icon name="lucide-calendar-clock" />
                                <span>Attendance Request</span>
                            </button>
                            <button
                                class="hr-dropdown-item"
                                @click="navigateToHR('/app/leave-application')"
                            >
                                <Icon name="lucide-calendar-days" />
                                <span>Leave Application</span>
                            </button>
                            <button
                                class="hr-dropdown-item"
                                @click="navigateToHR('/app/salary-slip')"
                            >
                                <Icon name="lucide-wallet" />
                                <span>Salary Slip</span>
                            </button>
                        </div>
                    </div>
                    <!-- TEAM MENU -->
                    <div class="team-menu-wrapper" data-tour="team-menu">
                        <Button
                            variant="ghost"
                            theme="gray"
                            size="sm"
                            class="quick-access-button team-menu-trigger"
                            @click.stop="
                                showTeamMenu = !showTeamMenu;
                                showHRMenu = false
                            "
                        >
                            <template #prefix>
                                <Icon name="lucide-users-round" />
                            </template>
                            Team
                            <template #suffix>
                                <Icon
                                    :name="showTeamMenu ? 'lucide-chevron-up' : 'lucide-chevron-down'"
                                />
                            </template>
                        </Button>
                        <!-- TEAM DROPDOWN -->
                        <div
                            v-if="showTeamMenu"
                            class="team-dropdown"
                            @click.stop
                        >
                            <div class="team-dropdown-header">
                                <div>
                                    <h4>Team Updates</h4>
                                    <p>Stay connected with your teammates</p>
                                </div>
                                <Icon name="lucide-users-round" />
                            </div>
                            <!-- TEAM TABS -->
                            <div class="team-tabs">
                                <button
                                    class="team-tab"
                                    :class="{ active: activeTeamTab === 'leave' }"
                                    @click="activeTeamTab = 'leave'"
                                >
                                    <Icon name="lucide-calendar-off" />
                                    On Leave
                                    <span>{{ teamLeaves.length }}</span>
                                </button>
                                <button
                                    class="team-tab"
                                    :class="{ active: activeTeamTab === 'dates' }"
                                    @click="activeTeamTab = 'dates'"
                                >
                                    <Icon name="lucide-calendar-heart" />
                                    Important Dates
                                    <span>{{ teamImportantDates.length }}</span>
                                </button>
                            </div>
                            <!-- ON LEAVE TAB -->
                            <div
                                v-if="activeTeamTab === 'leave'"
                                class="team-dropdown-list"
                            >
                                <div v-if="teamUpdatesLoading" class="team-empty-state"><span>Loading team updates...</span></div>
                                <div
                                    v-for="person in teamLeaves"
                                    :key="person.id"
                                    class="team-update-item"
                                >
                                    <Avatar
                                        :label="person.name"
                                        size="sm"
                                    />
                                    <div class="team-update-content">
                                        <strong>{{ person.name }}</strong>
                                        <span>{{ person.designation }}</span>
                                        <small>
                                            {{ formatTeamDate(person.from) }} – {{ formatTeamDate(person.to) }}
                                        </small>
                                    </div>
                                </div>
                                <div
                                    v-if="!teamUpdatesLoading && !teamLeaves.length"
                                    class="team-empty-state"
                                >
                                    <Icon name="lucide-calendar-check" />
                                    <span>No teammates currently on leave</span>
                                </div>
                            </div>
                            <!-- IMPORTANT DATES TAB -->
                            <div
                                v-else
                                class="team-dropdown-list"
                            >
                                <div v-if="teamUpdatesLoading" class="team-empty-state"><span>Loading important dates...</span></div>
                                <div
                                    v-for="item in teamImportantDates"
                                    :key="item.id"
                                    class="team-update-item"
                                >
                                    <div
                                        class="team-date-icon"
                                        :class="item.type === 'Birthday'
                                            ? 'birthday-icon'
                                            : 'event-icon'"
                                    >
                                        <Icon
                                            :name="item.type === 'Birthday'
                                                ? 'lucide-cake-slice'
                                                : item.type === 'Anniversary'
                                                    ? 'lucide-award'
                                                    : 'lucide-calendar-days'"
                                        />
                                    </div>
                                    <div class="team-update-content">
                                        <strong>{{ item.name }}</strong>
                                        <span>{{ item.description }}</span>
                                        <small>{{ formatTeamDate(item.date) }}</small>
                                    </div>
                                    <Badge
                                        :theme="item.type === 'Birthday' ? 'blue' : 'green'"
                                    >
                                        {{ item.type }}
                                    </Badge>
                                </div>
                                <div
                                    v-if="!teamUpdatesLoading && !teamImportantDates.length"
                                    class="team-empty-state"
                                >
                                    <Icon name="lucide-calendar-heart" />
                                    <span>No upcoming important dates</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <!-- MY TIMESHEET -->
                    <Button
                        variant="ghost"
                        theme="gray"
                        size="sm"
                        class="quick-access-button"
                        @click="navigateTo('/app/timesheet')"
                    >
                        <template #prefix>
                            <Icon name="lucide-calendar-clock" />
                        </template>
                        My Timesheet
                    </Button>
                </div>
            </section>
        </div>
        <!-- WEEKLY HOURS POPUP -->
        <div
            v-if="showWeeklyChart"
            class="chart-modal-backdrop"
            @click.self="closeWeeklyChart"
        >
            <section
                class="chart-modal"
                role="dialog"
                aria-modal="true"
                aria-labelledby="weekly-chart-title"
            >
                <div class="chart-modal-header">
                    <div>
                        <h3 id="weekly-chart-title">
                            Weekly Working Hours
                        </h3>
                        <p>Your productive hours for this week</p>
                    </div>
                    <button
                        type="button"
                        class="chart-close-button"
                        aria-label="Close weekly chart"
                        @click="closeWeeklyChart"
                    >
                        <Icon name="lucide-x" />
                    </button>
                </div>
                <div class="chart-modal-summary">
                    <div>
                        <span class="modal-total">{{ totalHours }}</span>
                        <span class="modal-target"> / {{ weeklyTarget }} hrs</span>
                    </div>
                    <Badge theme="green">
                        {{ weeklyPercentage }}% completed
                    </Badge>
                </div>
                <div class="modal-chart">
                    <div class="chart-y-axis" aria-hidden="true">
                        <span>10h</span>
                        <span>8h</span>
                        <span>6h</span>
                        <span>4h</span>
                        <span>2h</span>
                        <span>0h</span>
                    </div>
                    <div class="modal-chart-content">
                        <div
                            class="chart-grid-lines"
                            aria-hidden="true"
                        >
                            <span
                                v-for="line in 6"
                                :key="line"
                            ></span>
                        </div>
                        <div
                            v-for="day in weeklyData"
                            :key="day.label"
                            class="modal-chart-day"
                        >
                            <div class="modal-bar-area">
                                <div
                                    class="modal-chart-bar"
                                    :class="{
                                        'modal-chart-bar-today': day.today
                                    }"
                                    :style="{
                                        height: `${(day.hours / 10) * 100}%`
                                    }"
                                    :title="`${day.hours.toFixed(1)} hours`"
                                ></div>
                            </div>
                            <span class="modal-chart-hours">
                                {{ day.hours.toFixed(1) }}h
                            </span>
                            <span class="modal-chart-label">
                                {{ day.label }}
                            </span>
                        </div>
                    </div>
                </div>
                <div class="chart-modal-footer">
                    <span class="legend-dot"></span>
                    <span>Daily productive hours</span>
                    <span class="chart-target-note">
                        Daily target: 9 hours
                    </span>
                </div>
            </section>
        </div>
    </div>
</template>
<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { Avatar, Badge, Button, Icon, createResource } from 'frappe-ui'
// --------------------------------------------------
// EMPLOYEE PROFILE + TODAY'S ATTENDANCE
// Reuses the existing dashboard API.
// --------------------------------------------------
const employee = ref({
    name: 'Loading...',
    id: '',
    designation: '',
    image: null,
})
const isCheckedIn = ref(false)
const checkInTime = ref(null)
const checkOutTime = ref(null)
const showWeeklyChart = ref(false)
// Attendance action state
const isAttendanceSubmitting = ref(false)
const isDaySummaryLoaded = ref(false)
const attendanceMessage = ref('')
let attendanceMessageTimeout = null
const attendanceMessageType = ref('success')
const daySummaryResource = createResource({
    url: '/api/method/one_compliance.one_compliance.api.executive_dashboard.get_my_day_summary',
    auto: false,
})
function unwrapMessage(response) {
    return response?.message ?? response?.data?.message ?? response?.data ?? response
}
function formatTime(value) {
    if (!value) return null
    // Frappe commonly returns a time as "HH:mm:ss" or a datetime string.
    const timePart = String(value).includes(' ')
        ? String(value).split(' ').at(-1)
        : String(value)
    const match = timePart.match(/^(\d{1,2}):(\d{2})(?::\d{2})?$/)
    if (match) {
        const date = new Date()
        date.setHours(Number(match[1]), Number(match[2]), 0, 0)
        return date.toLocaleTimeString('en-IN', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true,
        })
    }
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) return String(value)
    return parsed.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
    })
}
async function loadDaySummary() {
    try {
        const response = await daySummaryResource.fetch()
        const result = unwrapMessage(response)
        if (!result || result.error) {
            console.error('Unable to load employee day summary:', result?.error)
            return
        }
        const details = result.employee_details || {}
        employee.value = {
            name: details.employee_name || 'Employee',
            id: details.employee_id || result.employee || '',
            designation: details.designation || '',
            image: details.avatar || null,
        }
        checkInTime.value = formatTime(result.check_in)
        checkOutTime.value = formatTime(result.check_out)
        isCheckedIn.value = Boolean(result.is_checked_in)
        isDaySummaryLoaded.value = true
    } catch (error) {
        console.error('Unable to load employee day summary:', error)
    }
}
function getAttendanceErrorMessage(error) {
    // Try to extract the actual Frappe validation message.
    const messages = error?.messages
    if (Array.isArray(messages) && messages.length) {
        const firstMessage = messages[0]
        return firstMessage?.message || firstMessage
    }
    const responseData =
        error?.response?.data ||
        error?.data ||
        {}
    if (responseData._server_messages) {
        try {
            const serverMessages = JSON.parse(
                responseData._server_messages
            )
            if (serverMessages.length) {
                const firstMessage = JSON.parse(
                    serverMessages[0]
                )
                return firstMessage.message || firstMessage
            }
        } catch (parseError) {
            console.error(
                'Unable to parse server message:',
                parseError
            )
        }
    }
    return (
        error?.message ||
        'Unable to record attendance. Please try again.'
    )
}
async function recordAttendance(logType) {
    if (isAttendanceSubmitting.value || !isDaySummaryLoaded.value) {
        return
    }
    isAttendanceSubmitting.value = true
    attendanceMessage.value = ''
    try {
        const response = await fetch(
            '/api/method/one_compliance.one_compliance.api.executive_dashboard.record_attendance',
            {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-Frappe-CSRF-Token': window.frappe.csrf_token,
                    'Accept': 'application/json',
                },
                body: new URLSearchParams({
                    log_type: logType,
                }).toString(),
            }
        )
        const responseData = await response.json()
        if (!response.ok) {
            const error = new Error(
                responseData.exception || 'Unable to record attendance.'
            )
            error.data = responseData
            throw error
        }
        const result = unwrapMessage(responseData)
        if (!result || !result.success) {
            throw new Error(
                result?.message || 'Attendance could not be recorded.'
            )
        }
        showAttendanceMessage(
            result.message ||
            (logType === 'IN'
                ? 'Check In recorded successfully.'
                : 'Check Out recorded successfully.'),
            'success'
        )
        await loadDaySummary()
    } catch (error) {
        console.error('Attendance action failed:', error)
        showAttendanceMessage(
            getAttendanceErrorMessage(error),
            'error'
        )
    } finally {
        isAttendanceSubmitting.value = false
    }
}
// --------------------------------------------------
// WEEKLY PRODUCTIVE HOURS
// Uses timesheet_working_hours from submitted Timesheets.
// --------------------------------------------------
const weeklyData = ref([])
const weeklyTarget = ref(0)
const totalHours = ref('0.0')
const weeklyHoursResource = createResource({
    url: '/api/method/one_compliance.one_compliance.api.executive_dashboard.get_weekly_working_hours_analysis',
    auto: false,
})
const weeklyPercentage = computed(() => {
    const target = Number(weeklyTarget.value) || 0
    const total = Number(totalHours.value) || 0
    if (target <= 0) return '0.0'
    return Math.min((total / target) * 100, 100).toFixed(1)
})
async function loadWeeklyHours() {
    try {
        const response = await weeklyHoursResource.fetch()
        const result = unwrapMessage(response)
        if (!result || result.error) {
            console.error('Unable to load weekly working hours:', result?.error)
            return
        }
        const totals = result.totals || {}
        weeklyTarget.value = 45
        totalHours.value = Number(totals.timesheet_working_hours || 0).toFixed(1)
        weeklyData.value = (result.daily || []).map((day) => ({
            label: day.day,
            hours: Number(day.timesheet_working_hours || 0),
            today: Boolean(day.is_today),
        }))
    } catch (error) {
        console.error('Unable to load weekly working hours:', error)
    }
}
// --------------------------------------------------
// HR DROPDOWN
// --------------------------------------------------
const showHRMenu = ref(false)
function navigateToHR(route) {
    showHRMenu.value = false
    showTeamMenu.value = false
    window.location.href = route
}
// --------------------------------------------------
// TEAM DROPDOWN
// --------------------------------------------------
const showTeamMenu = ref(false)
const activeTeamTab = ref('leave')
const teamLeaves = ref([])
const teamImportantDates = ref([])
const teamUpdatesLoading = ref(false)
function formatTeamDate(value) {
    if (!value) return ''
    const parsedDate = new Date(`${value}T00:00:00`)
    if (Number.isNaN(parsedDate.getTime())) return value
    return parsedDate.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
    })
}
async function loadTeamUpdates() {
    teamUpdatesLoading.value = true
    try {
        const response = await fetch(
            '/api/method/one_compliance.one_compliance.api.executive_dashboard.get_team_updates',
            { credentials: 'same-origin' }
        )
        if (!response.ok) throw new Error(`HTTP error: ${response.status}`)
        const result = await response.json()
        const data = result.message || {}
        teamLeaves.value = data.team_leaves || []
        teamImportantDates.value = data.important_dates || []
    } catch (error) {
        console.error('Unable to load team updates:', error)
    } finally {
        teamUpdatesLoading.value = false
    }
}
// --------------------------------------------------
// CLOSE HR AND TEAM MENUS ON OUTSIDE CLICK
// --------------------------------------------------
function handleOutsideMenuClick(event) {
    const clickedInsideHR = event.target.closest('.hr-menu-wrapper')
    const clickedInsideTeam = event.target.closest('.team-menu-wrapper')
    if (!clickedInsideHR) showHRMenu.value = false
    if (!clickedInsideTeam) showTeamMenu.value = false
}
onMounted(() => {
    document.addEventListener('click', handleOutsideMenuClick)
    loadDaySummary()
    loadWeeklyHours()
    loadTeamUpdates()
})
onBeforeUnmount(() => {
    document.removeEventListener('click', handleOutsideMenuClick)

    if (attendanceMessageTimeout) {
        clearTimeout(attendanceMessageTimeout)
        attendanceMessageTimeout = null
    }
})
// --------------------------------------------------
// QUICK ACCESS + WEEKLY CHART
// --------------------------------------------------
function navigateTo(route) {
    window.location.href = route
}
function openWeeklyChart() {
    showWeeklyChart.value = true
}
function closeWeeklyChart() {
    showWeeklyChart.value = false
}

// --------------------------------------------------
// aTTENDANCE FEEDBACK MESSAGE
// --------------------------------------------------
function showAttendanceMessage(message, type) {
    // Clear any previous dismissal timer.
    if (attendanceMessageTimeout) {
        clearTimeout(attendanceMessageTimeout)
    }

    attendanceMessage.value = message
    attendanceMessageType.value = type

    // Automatically hide the message after 7 seconds.
    attendanceMessageTimeout = setTimeout(() => {
        attendanceMessage.value = ''
        attendanceMessageTimeout = null
    }, 7000)
}
</script>
<style scoped>

/* =========================================================
   EMPLOYEE DASHBOARD TOOLBAR — MODERN DESIGN
========================================================= */

.associate-dashboard {
    position: relative;
    width: 100%;
    padding: 16px 16px 0;
    margin: 0;
    box-sizing: border-box;
    font-family: inherit;
}

/* =========================================================
   TOOLBAR GRID
========================================================= */

.associate-toolbar {
    position: relative;
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
    width: 100%;
    padding: 0 0 18px;
    box-sizing: border-box;
    background: transparent;
    border: none;
    overflow: visible;
}

.associate-toolbar::after {
    content: "";
    position: absolute;
    bottom: 0;

    /* Extend beyond the toolbar's inner padding */
    left: -16px;
    width: calc(100% + 32px);

    height: 1px;
    background: #e2e8f0;

    /* Subtle shadow beneath the divider */
    box-shadow:
        0 3px 5px rgba(15, 23, 42, 0.12),
        0 6px 12px rgba(15, 23, 42, 0.08);

    pointer-events: none;
}

/* =========================================================
   INDIVIDUAL TOOLBAR CARDS
========================================================= */

.toolbar-section {
    position: relative;
    display: flex;
    flex-direction: column;

    min-width: 0;
    min-height: 158px;

    padding: 19px 20px;
    box-sizing: border-box;

    background: #ffffff;
    border: 1px solid #e5eaf0;
    border-radius: 4px;

    box-shadow:
        0 2px 5px rgba(15, 23, 42, 0.045),
        0 6px 16px rgba(15, 23, 42, 0.055),
        0 12px 28px rgba(15, 23, 42, 0.025);

    transition:
        border-color 0.2s ease,
        box-shadow 0.2s ease,
        transform 0.2s ease;
}

.toolbar-section:hover {
    border-color: #dce4ec;
    box-shadow:
        0 2px 5px rgba(15, 23, 42, 0.035),
        0 8px 20px rgba(15, 23, 42, 0.055);
    transform: translateY(-1px);

}

/* Keep Quick Access dropdowns above the toolbar divider */
.quick-access-section:has(.hr-dropdown),
.quick-access-section:has(.team-dropdown) {
    z-index: 1400;
}

/* =========================================================
   SECTION HEADINGS
========================================================= */

/* =========================================================
   SHARED SECTION HEADING STRUCTURE
========================================================= */

.section-heading {
    display: flex;
    align-items: center;
    gap: 11px;

    width: 100%;
    min-height: 38px;
    margin: 0 0 4px;
    padding: 0 0 13px;

    box-sizing: border-box;

    color: #1e293b;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: -0.015em;
    line-height: 1.4;
}

.section-icon {
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

/* Actual SVG styling */
.section-icon :deep(svg) {
    width: 18px !important;
    height: 18px !important;
    color: #334155 !important;
    stroke: #334155 !important;
    opacity: 1 !important;
}

.section-icon :deep(svg path),
.section-icon :deep(svg line),
.section-icon :deep(svg circle),
.section-icon :deep(svg rect),
.section-icon :deep(svg polyline) {
    stroke: #334155 !important;
    opacity: 1 !important;
}
/* =========================================================
   1. EMPLOYEE PROFILE
========================================================= */

.employee-profile {
    display: flex;
    align-items: center;
    gap: 26px;
    min-height: 56px;
}

.employee-avatar {
    width: 56px;
    height: 56px;
    flex: 0 0 56px;
}

.employee-avatar :deep(> *) {
    width: 100% !important;
    height: 100% !important;
    min-width: 66px !important;
    min-height: 66px !important;
    border: 2px solid #f1f5f9;
    box-sizing: border-box;
}

/* Placeholder letter */
.employee-avatar :deep(.text-2xl) {
    font-size: 37px !important;
    line-height: 1 !important;
}

.employee-details {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
}

.employee-details h3 {
    margin: 0;
    color: #172033;
    font-size: 15px;
    font-weight: 650;
    line-height: 1.35;
    overflow-wrap: anywhere;
}

.employee-id {
    color: #94a3b8;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.025em;
}

.employee-designation-badge {
    align-self: flex-start;
    margin-top: 4px;
}

.employee-designation-badge :deep(*) {
    font-size: 10px;
}

.profile-footer {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 8px;
    margin-top: auto;
    padding-top: 13px;
}

.profile-status {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    margin-left: auto;

    color: #64748b;
    font-size: 11px;
    font-weight: 500;
}

.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #16a34a;
    box-shadow: 0 0 0 3px #dcfce7;
    flex-shrink: 0;
}

/* =========================================================
   2. ATTENDANCE
========================================================= */

.attendance-action {
    display: flex;
    align-items: center;
    flex-wrap: nowrap;
    gap: 10px;
    min-height: 40px;
}

.attendance-button {
    min-width: 112px;
    min-height: 34px;
    padding: 5px 12px;
    justify-content: center;
    border-radius: 7px;
    font-size: 12px;
    font-weight: 600;
}



.attendance-button :deep(.attendance-arrow-icon) {
    width: 17px !important;
    height: 17px !important;
    flex-shrink: 0;
}

.attendance-action :deep(.badge) {
    border-radius: 20px;
    font-size: 10px;
    font-weight: 550;
}

.attendance-times {
    display: flex;
    align-items: stretch;
    gap: 10px;
    margin-top: auto;
    padding-top: 13px;
}

.time-item {
    display: flex;
    flex: 1;
    flex-direction: column;
    justify-content: center;
    gap: 7px;
    min-width: 0;
    padding: 9px 10px;
    box-sizing: border-box;
    border: 1.5px solid #e8edf2;
    border-radius: 7px;
    box-shadow: 0 2px 5px rgba(15, 23, 42, 0.06);
}

.time-value {
    color: #263449;
    font-size: 13px;
    font-weight: 400;
    font-variant-numeric: tabular-nums;
}

.time-value {
    color: #263449;
    font-size: 13px;
    font-weight: 400;
    font-variant-numeric: tabular-nums;
}

.time-divider {
    width: 1px;
    height: 29px;
    margin: 0 16px;
    background: #e8edf2;
    flex-shrink: 0;
}

.attendance-feedback {
    flex: 1;
    min-width: 0;
    margin: 0;
    font-size: 11px;
    line-height: 1.4;
    overflow-wrap: anywhere;
}
.attendance-feedback.success {
    color: #15803d;
}

.attendance-feedback.error {
    color: #dc2626;
}

.attendance-status-badge {
    margin-left: auto;
    flex-shrink: 0;
}

.attendance-status-badge :deep(*) {
    font-size: 10px;
    font-weight: 500;
}

.time-label {
    display: inline-flex;
    flex-direction: row;
    align-items: center;
    gap: 5px;
    white-space: nowrap;
    font-size: 11px;
}

.time-label :deep(svg) {
    width: 15px;
    height: 15px;
    flex-shrink: 0;
}
/* =========================================================
   3. WEEKLY HOURS
========================================================= */

.weekly-summary {
    display: flex;
    align-items: center;
    flex-wrap: nowrap;
    gap: 7px;
    width: 100%;
    min-height: 38px;
    margin-top: 1px;
}

.weekly-total {
    display: flex;
    align-items: baseline;
    gap: 5px;
    flex-shrink: 0;
}

.weekly-hours {
    color: #172033;
    font-size: 27px;
    line-height: 1.2;
    font-weight: 550;
    letter-spacing: -1px;
    font-variant-numeric: tabular-nums;
}

.weekly-target {
    color: #94a3b8;
    font-size: 13px;
    font-weight: 500;
}

.chart-trigger {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 29px;
    height: 29px;
    min-width: 29px;
    flex-shrink: 0;
    margin-left: 2px;
    padding: 4px;
    background: #ffffff;
    color: #334155;
    border: 1px solid #dbeafe;
    border-radius: 4px;
    box-shadow: none;
}

.chart-trigger:hover {
    background: #f8fafc;
    color: #334155;
}

.chart-trigger :deep(svg) {
    display: block;
    width: 17px;
    height: 17px;
    margin: 0;
    flex-shrink: 0;
    color: #334155;
    stroke: #334155;
}

.chart-trigger :deep(.button-content) {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    margin: 0;
}

.weekly-percentage {
    margin-left: auto;
    color: #64748b;
    font-size: 12px;
    font-weight: 550;
    white-space: nowrap;
}

.weekly-progress-track {
    width: 100%;
    height: 6px;
    margin-top: 14px;
    overflow: hidden;
    background: #edf1f5;
    border-radius: 20px;
}

.weekly-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #16a34a, #22c55e);
    border-radius: inherit;
    transition: width 0.35s ease;
}

/* =========================================================
   4. QUICK ACCESS
========================================================= */

.quick-access-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-top: -5px;
}

.quick-access-button {
    display: flex;
    align-items: center;
    width: 100%;
    min-height: 34px;
    padding: 5px 9px;
    justify-content: flex-start;
    border-radius: 7px;
    color: #475569;
    font-size: 12px;
    font-weight: 500;
    transition:
        background 0.15s ease,
        color 0.15s ease;
}

.quick-access-button:hover {
    background: #f1f5f9;
    color: #172033;
}

.quick-access-button :deep(.button-content) {
    flex: 1;
}

.quick-access-button :deep(.suffix) {
    margin-left: auto;
}

.quick-access-button :deep(svg) {
    width: 15px;
    height: 15px;
}

/* =========================================================
   HR DROPDOWN
========================================================= */

.hr-menu-wrapper,
.team-menu-wrapper {
    position: relative;
    width: 100%;
}

.hr-menu-trigger,
.team-menu-trigger {
    width: 100%;
    justify-content: flex-start;
}

.hr-dropdown {
    position: absolute;
    top: calc(100% + 7px);
    left: 0;
    right: auto;
    z-index: 1200;

    width: 220px;
    padding: 6px;
    box-sizing: border-box;

    background: #ffffff;
    border: 1px solid #e8edf2;
    border-radius: 10px;

    box-shadow:
        0 4px 8px rgba(15, 23, 42, 0.06),
        0 14px 32px rgba(15, 23, 42, 0.12);
}

.hr-dropdown-item {
    display: flex;
    align-items: center;
    gap: 11px;
    width: 100%;
    padding: 10px 11px;

    border: none;
    border-radius: 7px;
    background: transparent;

    color: #475569;
    font-family: inherit;
    font-size: 12px;
    font-weight: 500;
    text-align: left;

    cursor: pointer;
    transition: background 0.15s ease, color 0.15s ease;
}

.hr-dropdown-item:hover {
    background: #f1f5f9;
    color: #172033;
}

.hr-dropdown-item :deep(svg) {
    width: 16px;
    height: 16px;
    color: #94a3b8;
    flex-shrink: 0;
}

/* =========================================================
   TEAM DROPDOWN
========================================================= */

.team-dropdown {
    position: absolute;
    top: calc(100% + 7px);
    left: 0;
    right: auto;
    z-index: 1300;

    width: 350px;
    max-width: min(350px, calc(100vw - 30px));
    padding: 0;

    color: #263449;
    background: #ffffff;
    border: 1px solid #e8edf2;
    border-radius: 11px;

    box-shadow:
        0 4px 8px rgba(15, 23, 42, 0.06),
        0 14px 32px rgba(15, 23, 42, 0.12);

    overflow: hidden;
}

.team-dropdown-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 15px 16px;
    border-bottom: 1px solid #edf0f4;
}

.team-dropdown-header h4 {
    margin: 0;
    color: #1e293b;
    font-size: 13px;
    font-weight: 650;
}

.team-dropdown-header p {
    margin: 4px 0 0;
    color: #94a3b8;
    font-size: 10px;
}

.team-dropdown-header > :deep(svg) {
    width: 19px;
    height: 19px;
    color: #94a3b8;
}

.team-tabs {
    display: flex;
    gap: 4px;
    padding: 0 12px;
    border-bottom: 1px solid #edf0f4;
}

.team-tab {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;
    min-width: 0;
    gap: 6px;
    padding: 12px 5px;

    border: 0;
    border-bottom: 2px solid transparent;
    background: transparent;

    color: #94a3b8;
    font-size: 10px;
    font-weight: 550;
    white-space: nowrap;

    cursor: pointer;
    transition: color 0.15s ease, border-color 0.15s ease;
}

.team-tab.active {
    color: #15803d;
    border-bottom-color: #16a34a;
    font-weight: 650;
}

.team-tab > :deep(svg) {
    width: 14px;
    height: 14px;
    flex-shrink: 0;
}

.team-tab span {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 17px;
    height: 17px;
    padding: 0 5px;
    border-radius: 20px;
    background: #f1f5f9;
    color: #64748b;
    font-size: 9px;
}

.team-dropdown-list {
    max-height: 270px;
    overflow-y: auto;
    overflow-x: hidden;
}

.team-update-item {
    display: flex;
    align-items: center;
    gap: 11px;
    padding: 12px 14px;
    border-bottom: 1px solid #f1f5f9;
    transition: background 0.15s ease;
}

.team-update-item:hover {
    background: #fafbfc;
}

.team-update-item:last-child {
    border-bottom: 0;
}

.team-update-content {
    display: flex;
    flex: 1;
    min-width: 0;
    flex-direction: column;
    gap: 4px;
}

.team-update-content strong {
    color: #334155;
    font-size: 11px;
    font-weight: 600;
}

.team-update-content span {
    color: #64748b;
    font-size: 10px;
}

.team-update-content small {
    color: #94a3b8;
    font-size: 9px;
}

.team-date-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 38px;
    height: 38px;
    flex-shrink: 0;
    border-radius: 10px;
}

.team-date-icon :deep(svg) {
    width: 19px;
    height: 19px;
}

.birthday-icon {
    color: #db2777;
    background: #fdf2f8;
}

.event-icon {
    color: #2563eb;
    background: #eff6ff;
}

.team-empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 9px;
    min-height: 125px;
    padding: 18px;
    color: #94a3b8;
    font-size: 11px;
    text-align: center;
}

.team-empty-state :deep(svg) {
    width: 23px;
    height: 23px;
}

/* =========================================================
   WEEKLY HOURS CHART MODAL
========================================================= */

.chart-modal-backdrop {
    position: fixed;
    inset: 0;
    z-index: 9999;

    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;

    background: rgba(15, 23, 42, 0.55);
    backdrop-filter: blur(3px);
}

.chart-modal {
    box-sizing: border-box;
    width: 100%;
    max-width: 640px;
    padding: 25px;

    color: #263449;
    background: #ffffff;
    border: 1px solid #e8edf2;
    border-radius: 14px;

    box-shadow: 0 20px 60px rgba(15, 23, 42, 0.2);
}

.chart-modal-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
}

.chart-modal-header h3 {
    margin: 0;
    color: #172033;
    font-size: 17px;
    line-height: 1.4;
    font-weight: 650;
}

.chart-modal-header p {
    margin: 5px 0 0;
    color: #94a3b8;
    font-size: 12px;
}

.chart-close-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    padding: 0;

    color: #64748b;
    background: #f1f5f9;
    border: 0;
    border-radius: 8px;

    cursor: pointer;
    transition: background 0.15s ease;
}

.chart-close-button:hover {
    background: #e2e8f0;
}

.chart-close-button :deep(svg) {
    width: 16px;
    height: 16px;
}

.chart-modal-summary {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-top: 22px;
}

.modal-total {
    color: #172033;
    font-size: 27px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
}

.modal-target {
    color: #94a3b8;
    font-size: 13px;
}

.modal-chart {
    display: flex;
    height: 250px;
    margin-top: 25px;
}

.chart-y-axis {
    box-sizing: border-box;
    width: 38px;
    flex: 0 0 38px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 0 8px 31px 0;
    text-align: right;
    font-size: 10px;
    line-height: 1;
    color: #94a3b8;
}

.modal-chart-content {
    position: relative;
    flex: 1;
    min-width: 0;
    display: flex;
    justify-content: space-around;
    gap: 12px;
}

.chart-grid-lines {
    position: absolute;
    inset: 0 0 31px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    pointer-events: none;
}

.chart-grid-lines span {
    display: block;
    width: 100%;
    border-top: 1px solid #edf0f4;
}

.modal-chart-day {
    position: relative;
    z-index: 1;
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.modal-bar-area {
    box-sizing: border-box;
    width: 100%;
    height: calc(100% - 31px);
    display: flex;
    align-items: flex-end;
    justify-content: center;
}

.modal-chart-bar {
    display: block;
    width: min(42px, 65%);
    min-height: 0;
    background: #bbdfc8;
    border-radius: 6px 6px 0 0;
    transition: height 0.3s ease;
}

.modal-chart-bar-today {
    background: #16a34a;
}

.modal-chart-hours {
    box-sizing: border-box;
    height: 19px;
    padding-top: 5px;
    color: #475569;
    font-size: 10px;
    line-height: 1;
    font-weight: 600;
    white-space: nowrap;
}

.modal-chart-label {
    height: 12px;
    color: #94a3b8;
    font-size: 11px;
    line-height: 1;
}

.chart-modal-footer {
    display: flex;
    align-items: center;
    gap: 7px;
    margin-top: 15px;
    padding-top: 13px;
    border-top: 1px solid #edf0f4;
    color: #94a3b8;
    font-size: 11px;
}

.chart-modal-footer .legend-dot {
    background: #16a34a;
}

.legend-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
}

.chart-target-note {
    margin-left: auto;
}

/* =========================================================
   RESPONSIVE LAYOUT
========================================================= */

@media (max-width: 1100px) {
    .associate-toolbar {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 600px) {
    .associate-dashboard {
        padding: 10px 10px 0;
    }

    .associate-toolbar {
        grid-template-columns: minmax(0, 1fr);
        gap: 12px;
        padding-bottom: 14px;
    }

    .toolbar-section {
        min-height: 145px;
        padding: 15px;
    }

    .chart-modal-backdrop {
        padding: 12px;
    }

    .chart-modal {
        padding: 19px 14px;
        border-radius: 12px;
    }

    .modal-chart {
        height: 210px;
    }

    .chart-target-note {
        font-size: 10px;
    }

    .team-dropdown {
        width: min(350px, calc(100vw - 30px));
    }
}

</style>
