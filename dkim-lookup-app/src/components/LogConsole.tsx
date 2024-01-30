import {useEffect, useRef } from 'react';

interface LogConsoleProps {
	log: string[];
	setLog: (log: string[]) => void;
}

export const LogConsole: React.FC<LogConsoleProps> = ({ log, setLog }) => {
	const scrollDiv = useRef<HTMLInputElement>(null);
	useEffect(() => {
		if (scrollDiv.current) {
			scrollDiv.current.scrollTop = scrollDiv.current.scrollHeight;
		}
	});

	return (
		<div>
			<div>Log: <button onClick={() => setLog([])}>Clear</button></div>
			<div style={{
				overflowY: 'scroll',
				paddingBottom: '2rem',
				backgroundColor: 'white',
				borderStyle: 'inset',
				borderWidth: '2px',
				height: '50vh',
			}}
				ref={scrollDiv} >
				{log.map((line, index) =>
					<div style={{ margin: 0, fontFamily: 'monospace' }} key={index}>{line}</div>
				)}
			</div>
		</div>
	);
};
