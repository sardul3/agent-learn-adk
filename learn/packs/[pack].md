---
title: Pack {{ $params.letter }}
description: '{{ $params.summary }}'
outline: [2, 3]
---

# Pack {{ $params.letter }} — {{ $params.title }}

{{ $params.summary }}

<ClientOnly>
  <PackDetail />
</ClientOnly>
