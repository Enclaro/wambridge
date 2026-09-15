# Wambridge Mobile Design

## Overview

Wambridge Mobile is a small network-audio controller for a physical speaker. It should feel like a receiver control panel translated into a phone utility: status first, transport obvious, no streaming-service theatre.

The canonical runtime visual tokens are Android resources under `app/src/main/res/values*` plus the shared `MobileUi` helper. This file documents their intent and must change with them when a durable decision changes.

**North Star:** quickly understand the speaker state and perform the next control action with one hand.

**Avoid:** artwork-led music-player layouts, album-cover decoration, animated backgrounds, hidden gestures, dense icon-only controls and migrating to Compose solely for appearance.

## Colors

Light roles:

- background: `#F3F6F8`
- surface: `#FFFFFF`
- alternate surface: `#E7EDF2`
- text: `#15202B`
- muted text: `#657382`
- action blue: `#3568B8`
- soft action surface: `#DCE7F7`
- border: `#D2DAE3`
- connection/success green: `#277A57` with soft success surface `#E5F3EB`
- danger: `#B74452`

Night mode uses the same resource names through `values-night`: background `#10151B`, surface `#171E26`, alternate surface `#232D38`, text `#EAF0F6`, action blue `#83AEFF`, border `#3A4654`, success `#71D1A2` with soft success surface `#1D3B2E`.

Blue means action/navigation. Green means healthy connection or successful state. Red means error/destructive action. State must also be expressed in text, not color alone.

## Typography

Use Android system sans. Existing runtime sizes are intentional:

- page title: 30sp bold
- section title: 18sp bold
- field/control text: 14–15sp
- compact labels: 13sp bold

Do not bundle fonts into this utility app.

## Layout

Keep the existing single-column `ScrollView` model on phones. Primary actions should be large enough for touch and grouped with the status or object they affect. Use clear section titles instead of extra navigation layers.

If a future large-screen layout is justified, first reuse the existing controls and state model. Do not fork a second UI tree only for tablets.

## Elevation & Depth

The app is flat by default. Cards separate with surface tone and a 1dp border. Buttons have no static elevation. Use Android ripple for press feedback.

## Shapes

The existing `MobileUi` helper owns shape values:

- field/button/status: 14dp radius
- cards: 20dp radius

Do not turn every row into a pill. Hardware/control semantics should remain crisp.

## Components

`MobileUi` is the canonical owner for shared page, header, card, status, field and button styling. Extend it instead of copying screen-local drawables or spacing constants.

- Primary button: action blue, high contrast.
- Secondary button: muted control surface.
- Quiet button: bordered surface.
- Danger button: red semantic surface.
- Status: short, readable and visually close to the controls it describes.
- Forms: keep native text editing behavior and explicit labels.

## Do's and Don'ts

Do keep the app lightweight, support native day/night resources, preserve visible status and make touch targets forgiving.

Do not add Compose, a UI framework, animation library, blur or image pipeline for cosmetics. Playback/network reliability and fast startup outrank decorative polish.
