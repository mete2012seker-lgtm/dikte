import { AnimatedListDemo } from "@/components/animated-list-demo"

export default function Home() {
  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-8 p-8">
      <h1 className="text-3xl font-semibold tracking-tight">
        Magic UI Animated List
      </h1>
      <AnimatedListDemo />
    </main>
  )
}
