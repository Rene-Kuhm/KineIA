export default function Home() {
  return (
    <div className="flex flex-col items-center min-h-screen p-8 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-50">
      <main className="flex flex-col items-center w-full max-w-4xl gap-8">
        <h1 className="text-4xl font-bold">KineIA</h1>
        
        {/* Placeholder for Chat */}
        <div className="w-full h-[600px] border border-slate-200 dark:border-slate-800 rounded-lg bg-white dark:bg-slate-950 flex items-center justify-center shadow-sm">
          <p className="text-slate-500 dark:text-slate-400">Chat interface will go here...</p>
        </div>
      </main>
    </div>
  );
}
