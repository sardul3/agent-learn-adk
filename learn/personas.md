---
title: Personas
layout: page
---

<script setup>
import { withBase } from 'vitepress'
import {
  VPTeamPage,
  VPTeamPageTitle,
  VPTeamMembers,
  VPTeamPageSection
} from 'vitepress/theme-without-fonts'

const customers = [
  {
    avatar: withBase('/personas/maya.svg'),
    name: 'Maya',
    title: 'Customer · chat',
    org: 'Meridian app / web',
    desc: '“Order MC-1048292 says delivered but I got nothing.” WISMO, POD-lie, missing items. She needs a true OMS answer, not a confident hallucination.',
  },
]

const ops = [
  {
    avatar: withBase('/personas/devon.svg'),
    name: 'Devon',
    title: 'Store ops lead',
    org: 'Banner store + BOPIS',
    desc: '“DC shorted SKU 884210 for tomorrow’s pickup wave — what do we tell customers?” Inventory truth, substitutes, delay, cancel.',
  },
  {
    avatar: withBase('/personas/priya.svg'),
    name: 'Priya',
    title: 'CX supervisor',
    org: 'Customer Operations Platform',
    desc: '“Agent wants a $180 refund — approve or deny with reason.” HITL, audit, policy citations. If you cannot reconstruct the trajectory, she will not sign off.',
  },
]
</script>

<VPTeamPage>
  <VPTeamPageTitle>
    <template #title>Who you serve</template>
    <template #lead>
      Every lab ticket belongs to someone. If a design does not name Maya, Devon, or Priya, it is not a Meridian design yet.
    </template>
  </VPTeamPageTitle>
  <VPTeamMembers size="medium" :members="customers" />
  <VPTeamPageSection>
    <template #title>Ops floor</template>
    <template #lead>
      Agents call OMS / ATP / payments. They do not replace those systems, and they do not move money above threshold without Priya.
    </template>
    <template #members>
      <VPTeamMembers size="small" :members="ops" />
    </template>
  </VPTeamPageSection>
</VPTeamPage>
