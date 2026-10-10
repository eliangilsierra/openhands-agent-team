# Android (Kotlin, Jetpack Compose, Material 3): UX reference

Load this file for Android specifications and reviews. It complements [the skill](../SKILL.md) and the
rules in `data/stacks/jetpack-compose.csv` (`ux_search.py --checklist --platform android`).

## Platform fundamentals

| Topic | Expectation |
| --- | --- |
| Components | Material 3 (`androidx.compose.material3`): `Scaffold`, `TopAppBar`, `NavigationBar` or `NavigationRail`, `ListItem`, `Card`, `Button` variants, `ModalBottomSheet`, `SnackbarHost`, `AlertDialog` |
| Navigation | 3-5 top-level destinations in a bottom bar on phones, a rail or drawer on larger windows; system back always works, predictive back supported |
| Layout | Edge-to-edge with insets; window size classes for compact, medium and expanded; list-detail on large screens |
| Touch | 48x48dp minimum target; 8dp between targets |
| Text | Material type scale in `sp`; layouts survive 200% font scale |
| Color | Material color roles, light and dark schemes, dynamic color where the brand allows it |
| Motion | Material motion; respect "remove animations" |
| Feedback | Snackbar for transient messages, dialogs for decisions, inline errors for forms |

## Specification checklist per screen

1. Purpose and entry points (navigation, deep link, notification).
2. Layout for compact and expanded windows; what moves to a second pane.
3. Components, using Material 3 first, and their content priority.
4. States: loading, empty, error with retry, offline, partial, success.
5. Input: keyboard type, IME action, validation and error messages, autofill.
6. Accessibility: TalkBack order and merged items, headings, content descriptions, state descriptions,
   touch targets, contrast in both themes, font scaling.
7. System: insets, back behaviour, rotation and process death, permissions with rationale.
8. Copy in string resources, plurals and RTL.

## Accessibility checks in Compose tests

```kotlin
composeTestRule.onNodeWithContentDescription("Delete order").assertHasClickAction()
composeTestRule.onNodeWithText("Orders").assertIsDisplayed()
composeTestRule.onNode(hasText("Retry") and hasClickAction()).performClick()
```

Pair them with Accessibility Scanner or the Compose accessibility test checks when the project has
them, and a manual TalkBack pass for new screens.

## Design tokens in Compose

```kotlin
private val LightColors = lightColorScheme(primary = Brand40, onPrimary = Color.White, /* ... */)
private val DarkColors = darkColorScheme(primary = Brand80, onPrimary = Brand20, /* ... */)

@Composable
fun AppTheme(dark: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = if (dark) DarkColors else LightColors, typography = AppTypography, content = content)
}
```

Check every `on*` and container pair with `contrast.py` (Compose `0xAARRGGBB` values are accepted).

## Common review findings

| Finding | Typical severity |
| --- | --- |
| Icon-only button without content description | HIGH |
| Touch target under 48dp | HIGH |
| Text clipped at large font scale | HIGH |
| Content under the status or navigation bar | MEDIUM |
| No empty or error state | HIGH |
| Hard-coded colors that break dark theme | MEDIUM |
| Custom back handling that breaks predictive back | MEDIUM |
| Placeholder used as the only field label | HIGH |
