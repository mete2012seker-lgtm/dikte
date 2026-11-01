"use client"

import { AnimatedList } from "@/components/ui/animated-list"

export function AnimatedListDemo() {
  return (
    <AnimatedList delay={1000} className="max-w-sm">
      <p>Item 1</p>
      <p>Item 2</p>
      <p>Item 3</p>
    </AnimatedList>
  )
}
