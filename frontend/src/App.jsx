import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Machines from './pages/Machines';
import MachineDetail from './pages/MachineDetail';
import Logs from './pages/Logs';
import Issues from './pages/Issues';
import IssueDetail from './pages/IssueDetail';
import Commands from './pages/Commands';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="machines" element={<Machines />} />
          <Route path="machines/:id" element={<MachineDetail />} />
          <Route path="logs" element={<Logs />} />
          <Route path="issues" element={<Issues />} />
          <Route path="issues/:id" element={<IssueDetail />} />
          <Route path="commands" element={<Commands />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
