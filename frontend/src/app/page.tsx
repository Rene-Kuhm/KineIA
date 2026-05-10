import { ChatWindow } from "@/components/chat/ChatWindow";

export default function Home() {
  return (
    <div className="h-[calc(100vh-3.5rem)] bg-slate-50 dark:bg-slate-900">
      <ChatWindow />
    </div>
  );
}
