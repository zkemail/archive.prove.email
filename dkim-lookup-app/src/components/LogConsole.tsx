import moment from 'moment';
import {useEffect, useRef } from 'react';

export type LogRecord = {
	message: string;
	date: Date;
};

interface LogConsoleProps {
	log: LogRecord[];
	setLog: (log: LogRecord[]) => void;
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
					<div style={{ margin: 0, fontFamily: 'monospace' }} key={index}>
						<span>
							{moment(line.date).format('YYYY-MM-DD HH:mm:ssZ')}
						</span>
						{' - ' + line.message}
					</div>
				)}
			</div>
		</div>
	);
};
